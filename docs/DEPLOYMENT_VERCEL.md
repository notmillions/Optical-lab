# Préparation au déploiement Vercel

**État vérifié le 18 novembre 2026 :** le frontend Vite produit un bundle statique valide. L’application complète n’est pas encore prête à être déclarée déployée : l’API FastAPI, sa base de matériaux et le raccordement Vercel restent à valider.

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

FastAPI doit être hébergé séparément sur un service compatible Python 3.11+, avec :

1. l’installation de `pyproject.toml` ;
2. une base SQLite initialisée à partir du snapshot autorisé, ou un stockage persistant équivalent ;
3. `OPTICAL_LAB_DB` configuré vers cette base ;
4. un endpoint `/api/v1/health` vérifiable publiquement ;
5. une politique CORS limitée à l’origine Vercel réelle.

Le frontend utilise maintenant `VITE_API_BASE_URL`, avec une valeur vide conservant le fonctionnement local. Le backend accepte les origines supplémentaires dans `OPTICAL_LAB_WEB_ORIGINS` (liste séparée par des virgules), tout en conservant les deux origines locales par défaut.

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

