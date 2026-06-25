"""Cadre à connecteurs : ajouter une source = écrire une sous-classe + @register.

Le reste de l'appli ne voit jamais les détails d'une source : chaque connecteur
renvoie directement des `CanonicalJob`.
"""
from __future__ import annotations

import abc
from collections.abc import Iterable, Iterator

from ..models import CanonicalJob

_REGISTRY: list[type["SourceConnector"]] = []


def register(cls: type["SourceConnector"]) -> type["SourceConnector"]:
    """Décorateur : enregistre un connecteur pour qu'il soit lancé à la collecte."""
    _REGISTRY.append(cls)
    return cls


def all_connectors() -> list["SourceConnector"]:
    return [cls() for cls in _REGISTRY]


class SourceConnector(abc.ABC):
    """Interface commune à toutes les sources."""

    name: str = "base"

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """True si la source a tout le nécessaire (clés API, etc.) pour tourner."""

    @abc.abstractmethod
    def fetch(self) -> Iterable[CanonicalJob]:
        """Récupère les offres et les renvoie déjà normalisées au schéma canonique."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Connector {self.name}>"
