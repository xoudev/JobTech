"""Importe chaque connecteur pour déclencher son enregistrement (@register)."""
from .base import SourceConnector, all_connectors, register  # noqa: F401

# L'import de ces modules suffit à enregistrer les connecteurs dans le registre.
from . import france_travail  # noqa: F401,E402
from . import adzuna  # noqa: F401,E402
from . import themuse  # noqa: F401,E402
from . import jsonld  # noqa: F401,E402
