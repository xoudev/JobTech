"""Configuration centrale de JobTech.

Toutes les valeurs sensibles (clés API) sont lues depuis l'environnement
(ou un fichier .env via python-dotenv). Voir .env.example.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv non installé : on se contente des vraies variables d'env
    pass


# --- Stockage ----------------------------------------------------------------
DB_PATH = os.getenv("JOBTECH_DB", "jobtech.db")


# --- Périmètre géographique : Île-de-France ----------------------------------
# Les 8 départements franciliens. Sert au filtrage côté France Travail.
IDF_DEPARTMENTS = ["75", "77", "78", "91", "92", "93", "94", "95"]

IDF_DEPT_NAMES = {
    "75": "Paris",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
}


# --- Périmètre métier : informatique -----------------------------------------
# Codes ROME de la famille M18 « Systèmes d'information et de télécommunications ».
# Les plus utiles : M1805 (études & dév. info), M1806 (conseil / MOA SI).
IT_ROME_CODES = [
    "M1801",  # Administration de systèmes d'information
    "M1802",  # Expertise et support en systèmes d'information
    "M1803",  # Direction des systèmes d'information
    "M1804",  # Études et développement de réseaux de télécoms
    "M1805",  # Études et développement informatique
    "M1806",  # Conseil et maîtrise d'ouvrage en systèmes d'information
    "M1810",  # Production et exploitation de systèmes d'information
]

# Mots-clés IT, pour les sources qui n'ont pas de filtre métier structuré.
IT_KEYWORDS = [
    "développeur", "developer", "data", "devops", "software",
    "ingénieur logiciel", "cybersécurité", "cloud", "sysadmin", "frontend",
    "backend", "fullstack",
]


# --- Source : France Travail (ex-Pôle Emploi) --------------------------------
# Inscription gratuite sur https://francetravail.io pour obtenir id + secret.
FT_CLIENT_ID = os.getenv("FT_CLIENT_ID")
FT_CLIENT_SECRET = os.getenv("FT_CLIENT_SECRET")
FT_TOKEN_URL = os.getenv(
    "FT_TOKEN_URL",
    "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
)
# Si l'auth renvoie "invalid_scope", essayer : "application_<CLIENT_ID> api_offresdemploiv2 o2dsoffre"
FT_SCOPE = os.getenv("FT_SCOPE", "api_offresdemploiv2 o2dsoffre")
FT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


# --- Source : Adzuna (agrégateur mondial, optionnel) -------------------------
# Inscription gratuite sur https://developer.adzuna.com
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
# Nombre de pages Adzuna à parcourir par collecte (50 offres/page).
ADZUNA_MAX_PAGES = int(os.getenv("ADZUNA_MAX_PAGES", "5"))


# --- Source : The Muse (fonctionne SANS clé) ---------------------------------
# Clé optionnelle pour des quotas plus élevés : https://www.themuse.com/developers/api/v2
THEMUSE_API_KEY = os.getenv("THEMUSE_API_KEY")
THEMUSE_MAX_PAGES = int(os.getenv("THEMUSE_MAX_PAGES", "5"))


# --- Source : JSON-LD générique (schema.org/JobPosting) ----------------------
# Liste de pages carrière / job boards (séparées par des virgules) qui embarquent
# leurs offres en JSON-LD. Un seul connecteur pour potentiellement des centaines
# de sites. Vide par défaut (connecteur inactif).
JSONLD_URLS = [u.strip() for u in os.getenv("JSONLD_URLS", "").split(",") if u.strip()]


# --- Réseau ------------------------------------------------------------------
HTTP_TIMEOUT = float(os.getenv("JOBTECH_HTTP_TIMEOUT", "30"))
USER_AGENT = os.getenv("JOBTECH_USER_AGENT", "JobTech/0.1 (+perso)")
