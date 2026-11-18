# QA navigateur — Playwright

Le parcours E2E de `apps/web` vérifie le chemin utilisateur réel :

1. démarrage de l'interface Vite et de l'API FastAPI ;
2. chargement du catalogue de quatre jeux de données RefractiveIndex.INFO épinglés ;
3. présence des contrôles accessibles et de leurs labels ;
4. calcul laser TMM via `POST /api/v1/simulations` ;
5. export JSON reproductible et CSV spectral depuis le navigateur.

Le test ne fabrique pas de constantes optiques, ne mocke pas les routes API et ne couvre pas la validation Touloukian/EKHI. Il vérifie le contrat d'intégration et le parcours d'interface ; les tests scientifiques Python restent la référence pour la physique.

## Prérequis locaux

- Python 3.11+ avec les dépendances du dépôt ;
- Node.js 22 et npm ;
- un navigateur Chromium installé pour Playwright ;
- un accès réseau lors du premier import des sources épinglées.

Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/verify_s1_pilots.py

cd apps/web
npm install
npx playwright install chromium
npm run e2e
```

`verify_s1_pilots.py` crée la base ignorée `data/processed/s1-integration.sqlite` et son cache source. Playwright la sélectionne automatiquement via `OPTICAL_LAB_DB`. Pour utiliser une autre base déjà initialisée :

```bash
OPTICAL_LAB_DB=data/processed/optical-lab.sqlite npm run e2e
```

La configuration démarre automatiquement l'API sur `127.0.0.1:8000` et Vite sur `127.0.0.1:5173`. Hors CI, elle réutilise un service déjà démarré ; en CI, elle exige les deux serveurs démarrés par Playwright. Les traces, captures et vidéos ne sont produites qu'en cas d'échec (ou conservées sur échec) dans le rapport Playwright.

## Limites du gap couvert

- Chromium est le seul navigateur installé par le socle minimal ; Firefox/WebKit restent à ajouter si la compatibilité multi-moteurs devient un objectif.
- La revue visuelle, l'accessibilité automatisée exhaustive et les mesures de performance ne sont pas déduites de ce test fonctionnel.
- Le test dépend de la disponibilité de la base pilote réelle ; une base absente ou un import réseau échoué doit être traité comme un prérequis manquant, pas comme une simulation réussie.
