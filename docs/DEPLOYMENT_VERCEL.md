# Préparation au déploiement Vercel

**État vérifié le 18 novembre 2026 :** le frontend Vite produit un bundle statique valide et son contrat de raccordement est testé. L’application complète nécessite toujours une API FastAPI publique, sa base de matériaux initialisée et des smoke tests distants.

## Conclusion

Le dépôt contient deux services distincts :

| Composant | Déploiement possible aujourd’hui | Raison |
|---|---|---|
| `apps/web` | Oui, comme preview statique | Vite génère `dist/` sans dépendance Python au build |
| `apps/api` | Pas comme frontend Vercel | FastAPI, dépendances Python, base SQLite et données importées sont nécessaires |
| Parcours V1 complet | Oui sous réserve du backend | Le frontend accepte `VITE_API_BASE_URL`; FastAPI et sa base restent un service séparé |

Un projet Vercel configuré uniquement sur `apps/web` peut afficher l’interface. Pour rendre le parcours V1 fonctionnel, il faut renseigner `VITE_API_BASE_URL` avec l’origine publique du service FastAPI : le proxy Vite vers `127.0.0.1:8000` n’existe qu’en développement local.

La base de matériaux de production n’est pas committée (`data/processed/` est ignoré) et l’API utilise actuellement SQLite via `OPTICAL_LAB_DB`. Cela renforce la nécessité d’héberger FastAPI séparément, avec un stockage et une initialisation maîtrisés.

## Configuration Vercel documentée

Lorsque le projet Vercel sera créé ou relié par un mainteneur authentifié, utiliser :

- **Root Directory** : `apps/web`
- **Framework preset** : `Vite`
- **Install Command** : `npm ci`
- **Build Command** : `npm run build`
- **Output Directory** : `dist`
- **Node.js** : version 22, comme dans la CI
- **Variable d’environnement** : `VITE_API_BASE_URL=https://<origine-publique-de-l-api>`

Cette configuration déploie le frontend statique. Elle devient le frontend V1 fonctionnel lorsque l’URL FastAPI est disponible et que son CORS autorise l’origine Vercel. Aucun `vercel.json` n’est ajouté volontairement : une règle de réécriture `/api` vers une URL inventée ou absente masquerait le blocage réel.

## Backend requis pour un déploiement fonctionnel

La configuration de référence pour ce service séparé se trouve dans
[DEPLOYMENT_FASTAPI.md](DEPLOYMENT_FASTAPI.md), avec `Dockerfile.api`,
`render.yaml` et un disque persistant. Vercel reste limité au frontend dans la
configuration actuelle.

FastAPI doit être hébergé séparément sur un service compatible Python 3.11+, avec :

1. l’installation de `pyproject.toml` ;
2. une base SQLite initialisée à partir du snapshot autorisé, ou un stockage persistant équivalent ;
3. `OPTICAL_LAB_DB` configuré vers cette base ;
4. un endpoint `/api/v1/health` vérifiable publiquement ;
5. une politique CORS limitée à l’origine Vercel réelle.

Le frontend utilise `VITE_API_BASE_URL` : une valeur vide conserve le proxy local uniquement lorsque Vite tourne en développement. Dans un build Vercel, une valeur absente ou invalide est affichée comme **BACKEND NON CONFIGURÉ** et ne peut pas être affichée comme une API connectée. Le backend accepte les origines supplémentaires dans `OPTICAL_LAB_WEB_ORIGINS` (liste séparée par des virgules), tout en conservant les deux origines locales par défaut.

## Contrat d’environnement

Frontend, au moment du build Vercel :

```dotenv
VITE_API_BASE_URL=https://optical-lab-api.example.com
```

Backend, au runtime :

```dotenv
OPTICAL_LAB_DB=/persistent/path/optical-lab.sqlite
OPTICAL_LAB_WEB_ORIGINS=https://optical-lab-web.vercel.app
```

`OPTICAL_LAB_WEB_ORIGINS` doit contenir l’origine exacte du navigateur, sans
chemin, et ne doit pas être remplacée par `*`. Après toute modification de
`VITE_API_BASE_URL`, il faut reconstruire le frontend : la variable est injectée
par Vite au build et n’est pas lue dynamiquement dans le navigateur.

## Smoke tests de raccordement

Les tests frontend vérifient les appels `/health` et `/capabilities`, les trois
routes de catalogue utilisées par l’interface, `POST /simulations` et
`POST /exports` sans toucher au solveur ni à l’importeur :

```bash
cd apps/web
npm test -- --run src/lib/api.test.ts
```

Le test CORS backend vérifie le pré-vol local et l’absence de wildcard pour une
origine non autorisée :

```bash
python -m pytest -q tests/test_api.py
```

Avant une mise en production, exécuter aussi ces quatre requêtes contre les
URLs publiques avec une base initialisée : santé, catalogue, simulation laser
et export JSON/CSV. Une réponse frontend `BACKEND NON CONFIGURÉ` indique une
variable Vercel manquante ; `API HORS LIGNE` indique ensuite un problème réseau,
de santé backend ou de CORS.

## Check local reproductible

Depuis la racine du dépôt :

```bash
./scripts/check_vercel_frontend.sh
```

Le check exécute `npm ci`, le typecheck TypeScript, les 14 tests Vitest, le build de production et vérifie que `apps/web/dist/index.html` existe. Il ne publie rien et ne nécessite aucun secret.

## Blocages d’authentification et de projet

Lors de l’audit :

- le CLI Vercel n’était pas installé dans l’environnement local ;
- aucun fichier `.vercel/` ni identifiant de projet n’était présent dans le dépôt ;
- aucune commande de liaison, d’authentification ou de déploiement n’a été exécutée ;
- aucun secret ou token n’a été demandé, lu ou ajouté.

La création ou la liaison du projet Vercel reste donc une action de mainteneur, après décision sur l’hébergement du backend.

## Conditions de sortie du blocage

Avant d’annoncer un déploiement V1 fonctionnel, il faut :

- une URL FastAPI de production et sa base de données initialisée ;
- le paramétrage de `VITE_API_BASE_URL` côté frontend ;
- CORS configuré pour le domaine Vercel exact ;
- un smoke test distant : santé, catalogue, simulation et export ;
- une vérification que les données et leur provenance sont disponibles dans l’environnement backend.

