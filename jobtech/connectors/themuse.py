"""Connecteur The Muse — fonctionne SANS clé d'API (quota plus élevé avec clé).

Sert de source « out-of-the-box » pour que l'appli tourne immédiatement.
On filtre sur Paris + catégories tech.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterator

import httpx

from .. import config
from ..models import CanonicalJob
from .base import SourceConnector, register

log = logging.getLogger(__name__)

_BASE = "https://www.themuse.com/api/public/jobs"
_IT_CATEGORIES = [
    "Software Engineering",
    "Data Science",
    "Data and Analytics",
    "IT",
    "Engineering",
]
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str | None:
    if not text:
        return text
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", text)).strip()


@register
class TheMuseConnector(SourceConnector):
    name = "themuse"

    def is_configured(self) -> bool:
        # Marche sans clé : toujours actif.
        return True

    def fetch(self) -> Iterator[CanonicalJob]:
        with httpx.Client(
            timeout=config.HTTP_TIMEOUT, headers={"User-Agent": config.USER_AGENT}
        ) as client:
            for page in range(0, config.THEMUSE_MAX_PAGES):
                params = [
                    ("page", page),
                    ("location", "Paris, France"),
                ]
                params += [("category", c) for c in _IT_CATEGORIES]
                if config.THEMUSE_API_KEY:
                    params.append(("api_key", config.THEMUSE_API_KEY))

                resp = client.get(_BASE, params=params)
                if resp.status_code == 400:  # au-delà de la dernière page
                    return
                resp.raise_for_status()
                data = resp.json() or {}
                results = data.get("results", []) or []
                if not results:
                    return
                for raw in results:
                    yield self._normalize(raw)
                if page >= (data.get("page_count", 1) - 1):
                    return

    def _normalize(self, raw: dict) -> CanonicalJob:
        locations = [loc.get("name") for loc in (raw.get("locations") or []) if loc.get("name")]
        location = ", ".join(locations) if locations else None
        remote = any("remote" in (l or "").lower() or "flexible" in (l or "").lower() for l in locations)
        department = "75" if any("paris" in (l or "").lower() for l in locations) else None

        company = (raw.get("company") or {}).get("name")
        levels = [lvl.get("name") for lvl in (raw.get("levels") or []) if lvl.get("name")]
        categories = [c.get("name") for c in (raw.get("categories") or []) if c.get("name")]

        return CanonicalJob(
            source=self.name,
            source_id=str(raw.get("id", "")),
            title=raw.get("name") or "",
            company=company,
            location=location,
            department=department,
            remote=remote or None,
            contract_type=raw.get("type"),
            description=_strip_html(raw.get("contents")),
            url=(raw.get("refs") or {}).get("landing_page") or "",
            salary=None,
            published_at=raw.get("publication_date"),
            tags=(levels + categories)[:15],
        )
