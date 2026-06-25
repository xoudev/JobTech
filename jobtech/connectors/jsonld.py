"""Connecteur générique schema.org/JobPosting.

C'est la façon dont Google for Jobs indexe le web : la plupart des sites
d'emploi sérieux embarquent leurs offres en JSON-LD
(`<script type="application/ld+json">`) pour le SEO. Ce connecteur lit une liste
de pages (configurable via JSONLD_URLS) et en extrait les offres — un seul
connecteur pour potentiellement des centaines de sites.

Limites : extraction par regex des blocs JSON-LD (pas de rendu JavaScript). Pour
les sites 100% dynamiques, il faudrait un connecteur dédié à base de navigateur.
"""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator

import httpx

from .. import config
from ..models import CanonicalJob
from .base import SourceConnector, register

log = logging.getLogger(__name__)

_LD_BLOCK_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_POSTAL_RE = re.compile(r"\b(\d{2})\d{3}\b")


def _strip_html(text):
    if not isinstance(text, str):
        return None
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", text)).strip() or None


def _first(value):
    """schema.org autorise objet OU liste ; on prend le premier élément utile."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def iter_jobpostings(node) -> Iterator[dict]:
    """Parcourt récursivement un document JSON-LD et renvoie les JobPosting."""
    if isinstance(node, list):
        for item in node:
            yield from iter_jobpostings(item)
    elif isinstance(node, dict):
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if any(str(t).split("/")[-1] == "JobPosting" for t in types if t):
            yield node
        else:  # descendre dans @graph, itemListElement, etc.
            for value in node.values():
                if isinstance(value, (list, dict)):
                    yield from iter_jobpostings(value)


def extract_jobpostings(html: str) -> list[dict]:
    """Extrait tous les JobPosting des blocs JSON-LD d'une page HTML."""
    postings: list[dict] = []
    for block in _LD_BLOCK_RE.findall(html):
        try:
            data = json.loads(block.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        postings.extend(iter_jobpostings(data))
    return postings


@register
class JsonLdConnector(SourceConnector):
    name = "jsonld"

    def is_configured(self) -> bool:
        return bool(config.JSONLD_URLS)

    def fetch(self) -> Iterator[CanonicalJob]:
        if not self.is_configured():
            log.warning("Connecteur JSON-LD inactif (JSONLD_URLS vide) — ignoré.")
            return
        with httpx.Client(
            timeout=config.HTTP_TIMEOUT,
            headers={"User-Agent": config.USER_AGENT},
            follow_redirects=True,
        ) as client:
            for url in config.JSONLD_URLS:
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError as exc:
                    log.warning("JSON-LD : échec sur %s (%s)", url, exc)
                    continue
                for raw in extract_jobpostings(resp.text):
                    yield self.normalize(raw, source_url=url)

    def normalize(self, raw: dict, source_url: str = "") -> CanonicalJob:
        org = _first(raw.get("hiringOrganization")) or {}
        company = org.get("name") if isinstance(org, dict) else None

        loc = _first(raw.get("jobLocation")) or {}
        address = loc.get("address") if isinstance(loc, dict) else None
        address = _first(address) or {}
        location = department = None
        if isinstance(address, dict):
            postal = str(address.get("postalCode") or "")
            locality = address.get("addressLocality")
            region = address.get("addressRegion")
            location = ", ".join(p for p in [locality, postal or None, region] if p) or None
            m = _POSTAL_RE.search(postal)
            if m:
                department = m.group(1)
        elif isinstance(address, str):
            location = address
            m = _POSTAL_RE.search(address)
            if m:
                department = m.group(1)

        employment = raw.get("employmentType")
        if isinstance(employment, list):
            employment = ", ".join(str(e) for e in employment)

        remote = None
        if str(raw.get("jobLocationType", "")).upper() == "TELECOMMUTE":
            remote = True

        identifier = raw.get("identifier")
        if isinstance(identifier, dict):
            identifier = identifier.get("value")
        source_id = str(identifier or raw.get("@id") or raw.get("url") or source_url)

        return CanonicalJob(
            source=self.name,
            source_id=source_id,
            title=_strip_html(raw.get("title")) or "",
            company=company,
            location=location,
            department=department,
            remote=remote,
            contract_type=str(employment) if employment else None,
            description=_strip_html(raw.get("description")),
            url=raw.get("url") or source_url,
            salary=_salary(raw.get("baseSalary")),
            published_at=raw.get("datePosted"),
            tags=[],
        )


def _salary(base) -> str | None:
    """Met en forme schema.org/MonetaryAmount -> texte lisible."""
    if not isinstance(base, dict):
        return None
    value = base.get("value")
    currency = base.get("currency") or ""
    if isinstance(value, dict):
        lo = value.get("minValue")
        hi = value.get("maxValue")
        single = value.get("value")
        unit = value.get("unitText") or ""
        if lo or hi:
            return f"{lo or hi} – {hi or lo} {currency} {unit}".strip()
        if single:
            return f"{single} {currency} {unit}".strip()
    return None
