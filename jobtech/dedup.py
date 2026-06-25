"""Déduplication : la même offre apparaît souvent sur plusieurs sources.

On calcule une empreinte stable à partir du (titre + entreprise + département)
normalisés. Deux offres qui produisent la même empreinte sont considérées
identiques et fusionnées au stockage.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata

from .models import CanonicalJob

# Repère les marqueurs de genre type "H/F", "F/H", "(H/F/X)", "W/M"...
_GENDER_RE = re.compile(r"\(?\b[hfwmx](?:[\s/\-]+[hfwmx])+\b\)?", re.IGNORECASE)
_NONWORD_RE = re.compile(r"[^a-z0-9 ]+")
_WS_RE = re.compile(r"\s+")


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_text(text: str | None) -> str:
    """Minuscule, sans accents, sans ponctuation ni marqueur H/F, espaces compactés."""
    if not text:
        return ""
    text = _strip_accents(text).lower()
    text = _GENDER_RE.sub(" ", text)
    text = _NONWORD_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return text.strip()


def fingerprint(job: CanonicalJob) -> str:
    """Empreinte de déduplication, stable d'une source à l'autre."""
    parts = [
        normalize_text(job.title),
        normalize_text(job.company),
        (job.department or "").strip(),
    ]
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()
