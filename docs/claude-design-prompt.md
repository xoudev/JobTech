# Prompt pour Claude — Design de l'interface JobTech

> Copie-colle le bloc ci-dessous dans Claude (mode **Artifacts** de préférence,
> sur claude.ai). Il est rédigé en français et autonome.

---

Tu es **designer produit + développeur front-end senior**. Conçois **et code**
l'interface web de **JobTech**, une application qui agrège les **offres d'emploi
en informatique en Île-de-France** (et plus largement en France).

## Le produit
JobTech collecte des offres IT depuis plusieurs sources (France Travail, Adzuna,
The Muse, pages carrière), les **dédoublonne**, les **enrichit** (stack technique
détectée, télétravail) et les présente dans une interface de recherche simple.
C'est un projet **perso**, utilisé par moi et mes amis développeurs pour ne pas
rater les bonnes offres en Île-de-France.

## Public & ton
- Développeurs / profils tech franciliens (du junior au senior).
- Ton : moderne, sobre, efficace, un peu « startup tech ». Pas corporate, pas surchargé.
- Langue de l'interface : **français**.

## Écran principal (90 % de l'usage) : recherche + liste d'offres
- Un **header** : logo « JobTech » + une ligne de stats (ex. « 1 248 offres · 4 sources »).
- Une **barre de filtres** :
  - champ de recherche plein texte — placeholder « Mots-clés : python, data, devops… » ;
  - sélecteur **département d'Île-de-France** : 75 Paris, 77 Seine-et-Marne,
    78 Yvelines, 91 Essonne, 92 Hauts-de-Seine, 93 Seine-Saint-Denis,
    94 Val-de-Marne, 95 Val-d'Oise ;
  - sélecteur **source** ;
  - case à cocher **Télétravail** ;
  - bouton **Rechercher**.
- Une **liste de cartes d'offres** (le cœur de l'écran).

## Modèle de données d'une offre (à afficher dans chaque carte)
- `title` — intitulé (ex. « Développeur Python (H/F) »)
- `company` — entreprise
- `location` — lieu (ex. « Paris (75) »)
- `department` — département (75–95)
- `contract_type` — CDI, CDD, stage, alternance, freelance
- `salary` — fourchette si disponible
- `published_at` — date de publication
- `source` — **badge** de la source (france_travail, adzuna, themuse…)
- `remote` — booléen télétravail
- `tags` — technos détectées (Python, React, AWS…), **cliquables** (un clic filtre
  sur cette techno)
- `url` — lien vers l'offre d'origine

## Composants & états à couvrir
- **Carte d'offre** : titre (lien), entreprise, lieu, type de contrat, salaire,
  date, badge source, badge télétravail, tags techno cliquables. Hiérarchie claire,
  scannable en 1 seconde.
- **État vide** (aucune offre) : message clair + invitation à lancer une collecte.
- **État de chargement** : skeletons.
- **Responsive** : **mobile d'abord** (on regarde souvent sur téléphone), puis desktop.
- *(Bonus)* un aperçu de **panneau de détail** d'une offre.

## Direction artistique
- **Dark mode** par défaut (fond sombre type `#0f1117`) + couleur d'accent tech
  (bleu/violet). Propose une variante claire si pertinent.
- Typo système, lisible ; espacements généreux mais **densité d'info correcte**
  (c'est une liste qu'on parcourt vite).
- Badges arrondis pour source / tags / télétravail ; la source a sa couleur propre.
- Micro-interactions discrètes (hover sur cartes et tags).
- **Accessibilité** : contrastes AA, focus visibles, HTML sémantique.

## Contraintes techniques
- Cible : intégrable facilement dans une appli **FastAPI + templates Jinja2 + CSS
  vanilla** (pas de framework lourd imposé).
- Fournis **d'abord** une version **HTML + CSS autonome** ; tu peux proposer une
  version **React** en option ensuite.
- Pas de dépendance runtime indispensable (CSS maison, ou Tailwind via CDN si tu
  justifies le choix).

## Livrable attendu
1. Un **artifact HTML + CSS complet et autonome**, avec **6–8 offres d'exemple
   réalistes** (postes IT franciliens), montrant la page de recherche remplie
   **et** l'état vide.
2. Les **design tokens** (couleurs, rayons, espacements) déclarés en variables CSS
   en tête de feuille de style.
3. Une **courte note** expliquant tes choix (palette, typo, hiérarchie).

## Critères de qualité
- Scannable, rapide, sans surcharge.
- Visuellement cohérent (espacements / rayons / couleurs systématiques).
- Mobile impeccable.
- Donne envie de cliquer sur les offres.

Commence directement par l'artifact, puis la note.
