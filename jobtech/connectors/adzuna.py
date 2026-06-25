"""Connecteur Adzuna — agrégateur mondial. Couvre la France, catégorie « IT Jobs ».

Optionnel : nécessite un app_id + app_key gratuits (https://developer.adzuna.com).
On restreint à l'Île-de-France via le paramètre `where`.
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

_BASE = "https://api.adzuna.com/v1/api/jobs/fr/search"
_POSTAL_RE = re.compile(r"\b(\d{2})\d{3}\b")


@register
class AdzunaConnector(SourceConnector):
    name = "adzuna"

    def is_configured(self) -> bool:
        return bool(config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY)

    def fetch(self) -> Iterator[CanonicalJob]:
        if not self.is_configured():
            log.warning("Adzuna non configuré (ADZUNA_APP_ID/KEY) — ignoré.")
            return
        with httpx.Client(
            timeout=config.HTTP_TIMEOUT, headers={"User-Agent": config.USER_AGENT}
        ) as client:
            for page in range(1, config.ADZUNA_MAX_PAGES + 1):
                params = {
                    "app_id": config.ADZUNA_APP_ID,
                    "app_key": config.ADZUNA_APP_KEY,
                    "results_per_page": 50,
                    "where": "Île-de-France",
                    "category": "it-jobs",
                    "content-type": "application/json",
                }
                resp = client.get(f"{_BASE}/{page}", params=params)
                resp.raise_for_status()
                results = (resp.json() or {}).get("results", []) or []
                if not results:
                    return
                for raw in results:
                    yield self._normalize(raw)

    def _normalize(self, raw: dict) -> CanonicalJob:
        loc = raw.get("location") or {}
        company = (raw.get("company") or {}).get("display_name")

        salary = None
        smin, smax = raw.get("salary_min"), raw.get("salary_max")
        if smin or smax:
            salary = f"{int(smin or smax):,} – {int(smax or smin):,} € / an".replace(",", " ")

        # Tentative d'extraction du département depuis le libellé du lieu.
        department = None
        areas = loc.get("area") or []
        for part in [loc.get("display_name", "")] + areas:
            m = _POSTAL_RE.search(str(part))
            if m:
                department = m.group(1)
                break

        return CanonicalJob(
            source=self.name,
            source_id=str(raw.get("id", "")),
            title=raw.get("title") or "",
            company=company,
            location=loc.get("display_name"),
            department=department,
            remote=None,
            contract_type=raw.get("contract_time") or raw.get("contract_type"),
            description=raw.get("description"),
            url=raw.get("redirect_url") or "",
            salary=salary,
            published_at=raw.get("created"),
            tags=[c for c in [(raw.get("category") or {}).get("label")] if c],
        )
