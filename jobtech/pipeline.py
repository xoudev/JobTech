"""Orchestration de la collecte : sources -> normalisation -> dédup -> stockage."""
from __future__ import annotations

import logging

from . import db
from .connectors import all_connectors
from .dedup import fingerprint

log = logging.getLogger(__name__)


def run_collection() -> dict:
    """Lance tous les connecteurs configurés. Retourne un récap par source."""
    db.init()
    recap: dict[str, dict] = {}

    for connector in all_connectors():
        if not connector.is_configured():
            log.info("⏭️  %s ignoré (non configuré)", connector.name)
            recap[connector.name] = {"status": "skipped", "new": 0, "seen": 0}
            continue

        log.info("▶️  Collecte : %s", connector.name)
        new_count = seen_count = 0
        try:
            for job in connector.fetch():
                if not job.title or not job.url:
                    continue
                job.fingerprint = fingerprint(job)
                if db.upsert(job):
                    new_count += 1
                else:
                    seen_count += 1
        except Exception as exc:  # une source en panne ne doit pas tout casser
            log.exception("❌ %s a échoué : %s", connector.name, exc)
            recap[connector.name] = {"status": "error", "error": str(exc), "new": new_count, "seen": seen_count}
            continue

        log.info("✅ %s : %d nouvelles, %d déjà connues", connector.name, new_count, seen_count)
        recap[connector.name] = {"status": "ok", "new": new_count, "seen": seen_count}

    return recap
