# JobTech 🇫🇷💻

Agrégateur d'**offres d'emploi informatiques en Île-de-France**. Il collecte les
offres depuis plusieurs sources, les normalise dans un format unique, supprime
les doublons, et te les présente dans une petite interface de recherche.

Pensé pour un usage perso (toi + tes potes) : **aucune infra lourde** — juste
Python et un fichier SQLite.

---

## Comment ça marche

```
Sources → Collecte → Normalisation → Déduplication → SQLite (+FTS5) → Recherche web
```

Chaque source est un **connecteur** indépendant. Ajouter une nouvelle source =
écrire une petite classe (voir [Ajouter une source](#ajouter-une-source)).

### Sources incluses

| Source | Clé requise ? | Périmètre |
|---|---|---|
| **The Muse** | ❌ non | Marche tout de suite, jobs tech à Paris |
| **France Travail** | ✅ gratuite | **Source principale** : départements 75–95, métiers IT (ROME M18) |
| **Adzuna** | ✅ gratuite | Agrégateur mondial, catégorie IT, filtré Île-de-France |

> Sans aucune clé, l'appli tourne déjà avec The Muse. Pour une vraie couverture
> francilienne, configure **France Travail** (5 min, gratuit).

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # puis remplis tes clés (optionnel pour démarrer)
```

## Utilisation

```bash
# 1. Collecter les offres (à relancer régulièrement, ex. via cron)
python -m jobtech collect

# 2. Lancer l'interface de recherche  →  http://127.0.0.1:8000
python -m jobtech serve

# Stats de la base
python -m jobtech stats
```

---

## Configurer France Travail (recommandé)

1. Crée un compte sur **https://francetravail.io**.
2. Crée une application et **souscris à l'API « Offres d'emploi v2 »**.
3. Récupère ton *identifiant client* et ta *clé secrète*.
4. Renseigne-les dans `.env` :

   ```env
   FT_CLIENT_ID=ton_identifiant
   FT_CLIENT_SECRET=ta_cle_secrete
   ```

5. `python -m jobtech collect`

> ⚠️ Si l'authentification renvoie une erreur `invalid_scope`, décommente dans
> `.env` la variante : `FT_SCOPE=application_<TON_CLIENT_ID> api_offresdemploiv2 o2dsoffre`.

Le périmètre (départements franciliens et codes métier ROME) se règle dans
[`jobtech/config.py`](jobtech/config.py).

---

## Automatiser la collecte (cron)

Pour rafraîchir les offres toutes les 6 h :

```cron
0 */6 * * * cd /chemin/vers/JobTech && .venv/bin/python -m jobtech collect >> collect.log 2>&1
```

---

## Ajouter une source

Crée `jobtech/connectors/ma_source.py` :

```python
from .base import SourceConnector, register
from ..models import CanonicalJob

@register
class MaSourceConnector(SourceConnector):
    name = "ma_source"

    def is_configured(self) -> bool:
        return True  # ou : bool(config.MA_CLE)

    def fetch(self):
        # ... récupère les données (API, RSS, JSON-LD...) ...
        yield CanonicalJob(
            source=self.name,
            source_id="123",
            title="Développeur Python",
            company="ACME",
            location="Paris (75)",
            department="75",
            url="https://...",
        )
```

Puis ajoute son import dans
[`jobtech/connectors/__init__.py`](jobtech/connectors/__init__.py). C'est tout —
le pipeline, la dédup et la recherche le prennent en charge automatiquement.

---

## Structure du projet

```
jobtech/
├── config.py            # géographie (IDF), métiers (ROME), clés API
├── models.py            # CanonicalJob : le schéma pivot
├── dedup.py             # empreinte de déduplication
├── db.py                # stockage SQLite + recherche FTS5
├── pipeline.py          # orchestration de la collecte
├── connectors/          # une source = un fichier
│   ├── base.py          # interface + registre
│   ├── france_travail.py
│   ├── adzuna.py
│   └── themuse.py
├── web/                 # interface FastAPI
│   ├── app.py
│   └── templates/index.html
└── __main__.py          # CLI : collect / serve / stats
```

---

## Notes légales

- On privilégie les **API officielles** (France Travail, Adzuna, The Muse), pas
  le scraping de sites comme LinkedIn/Indeed (interdit par leurs CGU + anti-bot).
- Usage personnel. Si tu ouvres la plateforme au public, vérifie les conditions
  de réutilisation de chaque source et les obligations RGPD.

## Pistes d'amélioration

- Déduplication floue (rapidfuzz) plutôt qu'empreinte exacte
- Connecteur générique `schema.org/JobPosting` (lit n'importe quelle page carrière)
- Extraction automatique de la stack technique depuis la description
- Détection fiable du télétravail
- Alertes e-mail / notifications sur nouveaux résultats
