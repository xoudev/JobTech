"""Schéma canonique d'une offre — le format pivot vers lequel chaque source converge."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CanonicalJob:
    """Une offre d'emploi normalisée, indépendante de sa source d'origine."""

    source: str                      # nom du connecteur, ex. "france_travail"
    source_id: str                   # identifiant de l'offre chez la source
    title: str
    url: str
    company: str | None = None
    location: str | None = None      # libellé brut, ex. "Paris (75)"
    department: str | None = None     # code à 2 chiffres, ex. "75"
    remote: bool | None = None        # télétravail (None = inconnu)
    contract_type: str | None = None  # CDI, CDD, stage, alternance, freelance...
    description: str | None = None
    salary: str | None = None
    published_at: str | None = None   # date ISO si dispo
    tags: list[str] = field(default_factory=list)  # stack technique, séniorité...

    # Rempli par le pipeline juste avant le stockage.
    fingerprint: str = ""
