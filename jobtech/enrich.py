"""Enrichissement des offres : stack technique + télétravail.

Étape post-normalisation, 100% hors-ligne : on lit le titre et la description
pour en déduire des tags techno (Python, React, AWS…) et un drapeau télétravail.
C'est ce qui fait la valeur d'un agrégateur *spécialisé IT* : pouvoir filtrer
par techno.
"""
from __future__ import annotations

import re
import unicodedata

from .models import CanonicalJob


def _norm(text: str) -> str:
    """Minuscule + sans accents, mais on GARDE la ponctuation (c++, c#, .net…)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower())


# Tag canonique -> fragments regex (sur texte normalisé). Volontairement
# conservateur pour éviter les faux positifs (ex. "vue" est un mot français,
# donc on exige "vue.js"/"vuejs" ; pas de "go" nu, trop ambigu).
_TECH_PATTERNS: dict[str, list[str]] = {
    "Python": [r"python"],
    "Java": [r"java(?!script)"],
    "JavaScript": [r"javascript"],
    "TypeScript": [r"typescript"],
    "Go": [r"golang"],
    "Rust": [r"rust"],
    "C++": [r"c\+\+"],
    "C#/.NET": [r"c#", r"\.net", r"dotnet", r"asp\.net"],
    "PHP": [r"php"],
    "Ruby": [r"ruby"],
    "Kotlin": [r"kotlin"],
    "Swift": [r"swift"],
    "Scala": [r"scala"],
    "React": [r"react"],
    "Angular": [r"angular"],
    "Vue.js": [r"vue\.?js", r"vuejs"],
    "Node.js": [r"node\.?js", r"nodejs"],
    "Django": [r"django"],
    "Flask": [r"flask"],
    "FastAPI": [r"fastapi"],
    "Spring": [r"spring boot", r"spring"],
    "Symfony": [r"symfony"],
    "Laravel": [r"laravel"],
    "Rails": [r"ruby on rails", r"rails"],
    "PostgreSQL": [r"postgresql", r"postgres"],
    "MySQL": [r"mysql"],
    "MongoDB": [r"mongodb", r"mongo"],
    "Redis": [r"redis"],
    "Elasticsearch": [r"elasticsearch", r"elastic search"],
    "Kafka": [r"kafka"],
    "Spark": [r"spark"],
    "Airflow": [r"airflow"],
    "Snowflake": [r"snowflake"],
    "AWS": [r"aws", r"amazon web services"],
    "Azure": [r"azure"],
    "GCP": [r"gcp", r"google cloud"],
    "Docker": [r"docker"],
    "Kubernetes": [r"kubernetes", r"k8s"],
    "Terraform": [r"terraform"],
    "Ansible": [r"ansible"],
    "Jenkins": [r"jenkins"],
    "GitLab CI": [r"gitlab ci", r"gitlab-ci"],
    "CI/CD": [r"ci/cd", r"ci cd", r"cicd"],
    "TensorFlow": [r"tensorflow"],
    "PyTorch": [r"pytorch"],
    "scikit-learn": [r"scikit-learn", r"scikit learn", r"sklearn"],
    "Pandas": [r"pandas"],
    "Linux": [r"linux"],
    "GraphQL": [r"graphql"],
    "REST": [r"restful", r"rest api", r"api rest"],
    "Microservices": [r"micro-?services?"],
}

# Compilation : chaque tag -> une regex avec frontières non-alphanumériques.
_COMPILED: list[tuple[str, re.Pattern]] = [
    (tag, re.compile(r"(?<![a-z0-9])(?:" + "|".join(frags) + r")(?![a-z0-9])"))
    for tag, frags in _TECH_PATTERNS.items()
]

# Télétravail : signaux positifs / négatifs (texte normalisé, sans accents).
_REMOTE_POS = re.compile(
    r"teletravail|remote|travail a distance|distanciel|home ?office|"
    r"work from home|wfh|hybride"
)
_REMOTE_NEG = re.compile(
    r"(?:pas|aucun|sans|non|zero|0)\s+(?:de\s+)?(?:teletravail|remote)|"
    r"presentiel\s+(?:uniquement|obligatoire|requis)|"
    r"sur\s+site\s+(?:uniquement|obligatoire)|"
    r"100\s*%?\s*(?:sur\s+site|presentiel)|no\s+remote|fully\s+on-?site|on-?site\s+only"
)


def extract_tech_tags(text: str | None) -> list[str]:
    """Renvoie les technos détectées dans le texte (sans doublon, ordre stable)."""
    if not text:
        return []
    t = _norm(text)
    return [tag for tag, rx in _COMPILED if rx.search(t)]


def detect_remote(text: str | None) -> bool | None:
    """True (télétravail), False (présentiel explicite), None (inconnu)."""
    if not text:
        return None
    t = _norm(text)
    if _REMOTE_NEG.search(t):
        return False
    if _REMOTE_POS.search(t):
        return True
    return None


def enrich(job: CanonicalJob) -> CanonicalJob:
    """Complète l'offre en place : ajoute les tags techno, déduit le télétravail."""
    text = f"{job.title or ''} . {job.description or ''}"
    detected = extract_tech_tags(text)
    # Fusion avec les tags déjà fournis par la source, sans doublon, plafonné.
    merged = list(dict.fromkeys([*(job.tags or []), *detected]))
    job.tags = merged[:20]

    if job.remote is None:
        job.remote = detect_remote(text)
    return job
