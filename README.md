# Optical Lab

**Travail pratique scientifique — base de matériaux et laboratoire virtuel de simulation optique.**

> **État : base S6 livrée, documentation S7 en préparation.** Le dépôt contient un pilote d'ingestion, de TMM, de sources spectrales, d'API, d'interface et d'exports. La validation expérimentale Touloukian/EKHI et la qualification de la V1 complète restent ouvertes.

## Vision
Choisir une source lumineuse (**laser / soleil / lampe**), sélectionner les jeux de constantes optiques sourcés pour chaque matériau, construire un empilement de couches planes, puis calculer et visualiser la réflectance **R**, la transmittance **T**, l'absorptance **A** et leurs spectres.

- **V1 — Option C :** multicouches planes, méthode des matrices de transfert (TMM), Python/FastAPI, React/Three.js et visualisation synchronisée.
- **V2 :** objets 3D libres (lentilles, prismes, miroirs), ray tracing et détecteurs via un moteur distinct.
- **Science :** données [RefractiveIndex.INFO](https://refractiveindex.info/) et validation à partir de *Thermophysical Properties of Matter* de Touloukian (volumes radiatifs 7, 8 ; 9 selon besoins).

## Documents
- [PRD / Cahier des charges](docs/PRD.md)
- [Architecture et contrats](docs/ARCHITECTURE.md)
- [Démarche scientifique](docs/SCIENTIFIC_METHOD.md)
- [Roadmap](docs/ROADMAP.md) · [Sprints](docs/SPRINTS.md) · [Backlog](docs/BACKLOG.md)
- [Qualité et tests](docs/TEST_PLAN.md) · [Gouvernance des données](docs/DATA_GOVERNANCE.md)
- [ADR 0001 — Option C](docs/adr/0001-evolutive-v1-tmm-v2-raytracing.md)
- [Contribution](CONTRIBUTING.md) · [Instructions aux agents](AGENTS.md)

## Stack envisagée
Python, PyYAML, NumPy/SciPy, [tmm](https://github.com/sbyrnes321/tmm), SQLite, FastAPI/Pydantic ; React, TypeScript, Vite, React Three Fiber / Three.js et Plotly ; Pytest, Vitest, Playwright.

## Démonstration scientifique cible
Laser 532 nm → air / SiO₂ (100 nm réglables) / cuivre (substrat semi-infini) → résultats TMM pour angles et polarisations s/p → graphiques spectraux et coupe 3D explicitement illustrative. Les références et intervalles de validité des données doivent être conservés.

## Développement
GitHub est la source de vérité. Développement dans un checkout Git sur Mac ou dans Work, sur branches dédiées, puis pull requests vérifiées avant intégration dans `main`. Ne pas faire de modifications simultanées non synchronisées sur une même branche.

## Installation et reproduction

Depuis la racine, avec Python 3.11+ et Node.js 22 :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff check apps packages tests scripts
python -m pytest -q
python scripts/check_docs.py
```

Puis, pour le frontend :

```bash
cd apps/web
npm install
npm run typecheck
npm test
npm run build
```

Pour importer les quatre jeux RefractiveIndex.INFO épinglés et vérifier le parcours réel :

```bash
cd <racine-du-dépôt>
python -m packages.material_data --db data/processed/s1-integration.sqlite
python scripts/verify_s1_pilots.py
python scripts/verify_v1_demo.py
```

L'import initial nécessite le réseau; `--offline` réutilise ensuite le cache local. Les fixtures `data/fixtures/` sont synthétiques et réservées aux tests. Pour les limites et les commandes détaillées, voir [docs/EXECUTION_STATUS.md](docs/EXECUTION_STATUS.md).

La vue Three.js est illustrative et pilotée par la configuration/réponse de calcul. Dans la réponse TMM, `T` est le flux entrant dans le substrat semi-infini, pas le flux traversant sa face arrière.

## Rapport de livraison

Le rapport est disponible en source LaTeX dans [docs/report/optical-lab-v1-report.tex](docs/report/optical-lab-v1-report.tex). Aucun PDF n'est commité lorsque la chaîne LaTeX n'est pas disponible dans l'environnement.

## Licences et données
Ce dépôt est **public**, mais aucune licence de code n'est accordée tant qu'un fichier `LICENSE` n'est pas explicitement choisi. Ne pas commiter les pages numérisées des livres Touloukian ni redistribuer de données externes sans avoir vérifié leurs licences. Les données brutes volumineuses restent hors Git.

## Développement — services locaux

- [Installer et exécuter les services](docs/S0_SETUP.md)
- Frontend : `cd apps/web && npm install && npm run dev`
- Backend : `python -m uvicorn apps.api.main:app --reload --port 8000`
- Frontend : `cd apps/web && npm run dev`
