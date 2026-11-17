# Optical Lab

**Travail pratique scientifique — base de matériaux et laboratoire virtuel de simulation optique.**

> **État : Sprint S0 (cadrage).** Les documents décrivent une cible à implémenter. Aucun moteur de calcul, backend ni visualiseur 3D n'est encore livré.

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

## Licences et données
Ce dépôt est **public**, mais aucune licence de code n'est accordée tant qu'un fichier `LICENSE` n'est pas explicitement choisi. Ne pas commiter les pages numérisées des livres Touloukian ni redistribuer de données externes sans avoir vérifié leurs licences. Les données brutes volumineuses restent hors Git.
