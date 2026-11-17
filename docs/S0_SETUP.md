# Sprint S0 — Installation et reprise

## Prérequis
- Python 3.11+ (CI : 3.12)
- Node.js 22 et npm
- Git ; navigateur avec WebGL pour le rendu 3D

## Backend FastAPI
Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m uvicorn apps.api.main:app --reload --port 8000
```

Endpoints disponibles :
- http://127.0.0.1:8000/api/v1/health
- http://127.0.0.1:8000/api/v1/capabilities
- http://127.0.0.1:8000/docs
- `POST /api/v1/scenes/validate` (validation **syntaxique uniquement**).

## Frontend Three.js
Dans un second terminal :

```bash
cd apps/web
npm install
npm run dev
```

Ouvrir http://localhost:5173/ et manipuler l'aperçu de couches. Vite relaie `/api` vers le port 8000. Le moteur scientifique n'est **pas encore** intégré ; le bouton de calcul et les valeurs R/T/A restent volontairement indisponibles.

## Qualité
```bash
python -m ruff check apps packages tests
python -m pytest -q
cd apps/web
npm run typecheck
npm test
npm run build
```

Le workflow `.github/workflows/ci.yml` doit exécuter les mêmes vérifications sur GitHub. Les commandes doivent être confirmées par l'exécution réelle avant de clore le Sprint S0.

## Contrats scientifiques S0
`apps/api/models.py` définit les scènes planes, source laser/soleil/lampe, incidences, couches et métadonnées de datasets. `packages/optical_core/interfaces.py` définit les ports du matériau, de la source et du solveur. Les exemples `Cu/EXAMPLE` et `SiO2/EXAMPLE` dans la documentation servent uniquement à la validation de schéma, **pas** à produire de vraies propriétés optiques.

## Reprise dans Codex Cloud
Sur la branche `feat/S0-foundations` ou après sa fusion : inspecter la PR, vérifier CI, ajouter les corrections si nécessaire puis suivre `docs/AUTONOMOUS_PLAN.md` à partir de M1. **Ne pas démarrer un second Sprint S0 sur main** sans avoir réconcilié cette branche.
