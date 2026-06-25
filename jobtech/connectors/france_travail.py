"""Connecteur France Travail (ex-Pôle Emploi) — API officielle « Offres d'emploi v2 ».

Source reine pour le marché français : on filtre par départements franciliens
et par codes ROME de l'informatique. Auth OAuth2 client_credentials.

Inscription gratuite : https://francetravail.io
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

_CONTENT_RANGE_RE = re.compile(r"/(\d+)\s*$")


def _parse_total(content_range: str | None) -> int | None:
    """Extrait le total depuis l'en-tête Content-Range « offres 0-149/1234 »."""
    if not content_range:
        return None
    m = _CONTENT_RANGE_RE.search(content_range)
    return int(m.group(1)) if m else None


@register
class FranceTravailConnector(SourceConnector):
    name = "france_travail"

    def is_configured(self) -> bool:
        return bool(config.FT_CLIENT_ID and config.FT_CLIENT_SECRET)

    def _get_token(self, client: httpx.Client) -> str:
        resp = client.post(
            config.FT_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": config.FT_CLIENT_ID,
                "client_secret": config.FT_CLIENT_SECRET,
                "scope": config.FT_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def fetch(self) -> Iterator[CanonicalJob]:
        if not self.is_configured():
            log.warning("France Travail non configuré (FT_CLIENT_ID/SECRET) — ignoré.")
            return
        departments = ",".join(config.IDF_DEPARTMENTS)
        with httpx.Client(
            timeout=config.HTTP_TIMEOUT, headers={"User-Agent": config.USER_AGENT}
        ) as client:
            token = self._get_token(client)
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            for rome in config.IT_ROME_CODES:
                yield from self._search_rome(client, headers, rome, departments)

    def _search_rome(
        self, client: httpx.Client, headers: dict, rome: str, departments: str
    ) -> Iterator[CanonicalJob]:
        start, page = 0, 150
        # L'API plafonne à 1150 résultats (premier indice <= 1000).
        while start <= 1000:
            end = min(start + page - 1, 1149)
            params = {
                "codeROME": rome,
                "departement": departments,
                "range": f"{start}-{end}",
                "sort": 1,  # tri par date décroissante
            }
            resp = client.get(config.FT_SEARCH_URL, headers=headers, params=params)
            if resp.status_code == 204:  # aucun résultat
                return
            resp.raise_for_status()
            results = (resp.json() or {}).get("resultats", []) or []
            for raw in results:
                yield self._normalize(raw)

            total = _parse_total(resp.headers.get("Content-Range"))
            start += page
            if not results or (total is not None and start >= total):
                return

    def _normalize(self, raw: dict) -> CanonicalJob:
        lieu = raw.get("lieuTravail") or {}
        code_postal = (lieu.get("codePostal") or "").strip()
        department = code_postal[:2] if len(code_postal) >= 2 else None
        entreprise = raw.get("entreprise") or {}
        salaire = raw.get("salaire") or {}
        origine = raw.get("origineOffre") or {}

        tags = [c.get("libelle") for c in (raw.get("competences") or []) if c.get("libelle")]

        return CanonicalJob(
            source=self.name,
            source_id=str(raw.get("id", "")),
            title=raw.get("intitule") or "",
            company=entreprise.get("nom"),
            location=lieu.get("libelle"),
            department=department,
            remote=None,
            contract_type=raw.get("typeContratLibelle") or raw.get("typeContrat"),
            description=raw.get("description"),
            url=origine.get("urlOrigine") or "",
            salary=salaire.get("libelle"),
            published_at=raw.get("dateCreation"),
            tags=tags[:15],
        )
