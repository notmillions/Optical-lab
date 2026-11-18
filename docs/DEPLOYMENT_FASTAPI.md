# Déploiement séparé de l'API FastAPI

## Cible retenue

La cible de référence est un service web Docker sur Render, séparé du site
statique Vercel. Cette cible est adaptée au dépôt parce que Render sait construire
un Dockerfile depuis un monorepo et attacher un disque persistant à un service.
SQLite ne doit pas être placée dans le système de fichiers par défaut du service :
ce système est éphémère. Le fichier de production est donc fixé à
`/var/lib/optical-lab/optical-lab.sqlite`, sous le disque déclaré dans
`render.yaml`.

La présence du fichier `render.yaml` ne crée ni service ni URL. La création du
service doit être faite par un mainteneur connecté à Render.

## Ce que le dépôt fournit

- `Dockerfile.api` : image minimale de l'API, sans frontend ;
- `.dockerignore.api` : exclut les artefacts locaux et le frontend ;
- `render.yaml` : service Docker, health check, variable SQLite et disque ;
- `scripts/start_api.py` : importe le catalogue complet si la base persistante
  n'est pas marquée comme initialisée, puis lance Uvicorn ;
- `Dockerfile.api` : télécharge au build l'archive du commit épinglé
  `e6d15e364f70de1cad8a96a20f75689f2fba8b21`, vérifie qu'il s'agit du snapshot
  attendu par l'importeur et conserve l'arbre YAML dans l'image ;
- l'import parcourt `database/data/main/**/nk/*.yml` et garde dans SQLite la
  provenance ainsi que les résultats `partial`, `unsupported` et `invalid`.

## Variables d'environnement

Les variables de bootstrap sont explicites dans `render.yaml` :

| Variable | Valeur de production | Rôle |
|---|---|---|
| `OPTICAL_LAB_DB` | `/var/lib/optical-lab/optical-lab.sqlite` | SQLite sur le disque persistant |
| `OPTICAL_LAB_SOURCE_ROOT` | `/opt/refractiveindex.info-database` | arbre du snapshot inclus dans l'image |
| `OPTICAL_LAB_CATALOG_MARKER` | `/var/lib/optical-lab/catalog-bootstrap.json` | état atomique du bootstrap terminé |
| `OPTICAL_LAB_WEB_ORIGINS` | à renseigner | origines CORS Vercel, séparées par des virgules |
| `PORT` | fourni par Render | port d'écoute Uvicorn |

Le snapshot n'est pas configurable au runtime : le commit est épinglé dans le
Dockerfile et contrôlé contre celui utilisé par l'importeur.

## Création du service

1. Créer un nouveau Web Service Render depuis le dépôt GitHub.
2. Choisir le runtime Docker et le fichier `Dockerfile.api` (ou créer le service
   depuis le Blueprint `render.yaml`).
3. Conserver le disque monté sur `/var/lib/optical-lab`. Une SQLite placée
   ailleurs serait perdue lors d'un redémarrage ou redéploiement.
4. Renseigner `OPTICAL_LAB_WEB_ORIGINS` avec l'origine exacte du frontend Vercel,
   par exemple l'origine fournie par le projet Vercel au moment de sa création.
   Ne pas ajouter de chemin `/`, ni inventer une URL dans le dépôt. Plusieurs
   origines peuvent être séparées par des virgules.
5. Déployer et vérifier `/api/v1/health` puis `/api/v1/materials`.

Au build de l'image, le service récupère l'arbre complet du snapshot
RefractiveIndex.INFO épinglé. Au premier démarrage, `start_api.py` importe tous
les fichiers découverts dans la SQLite persistante et écrit le marqueur
`OPTICAL_LAB_CATALOG_MARKER` après la transaction. Les redémarrages ultérieurs
réutilisent la base et le marqueur sans rescanner les sources. Une base pilote
non marquée est volontairement réimportée et mise à niveau vers le catalogue
complet.

## Initialisation manuelle ou réparation contrôlée

Pour initialiser une base locale ou une base montée sur un shell du service :

```bash
export OPTICAL_LAB_DB=/var/lib/optical-lab/optical-lab.sqlite
export OPTICAL_LAB_SOURCE_ROOT=/opt/refractiveindex.info-database
python -m packages.material_data \
  --source-root "$OPTICAL_LAB_SOURCE_ROOT" \
  --db "$OPTICAL_LAB_DB" \
  --coverage-report /var/lib/optical-lab/catalog-coverage.json
```

La commande utilise le même snapshot et les mêmes contrôles de checksum que le
bootstrap automatique. Elle doit être exécutée sur le service qui possède le
disque : le disque Render n'est accessible ni au build ni à un job séparé.

La base et le rapport de couverture ne sont pas committés dans Git. Ne pas
utiliser `data/processed/` en production et ne pas copier une SQLite dans
l'image Docker : ces chemins font partie du système de fichiers éphémère de
build/runtime. L'arbre YAML du snapshot est, lui, une donnée de build immuable
dans l'image.

## CORS et raccordement Vercel

Le backend conserve les origines locales et ajoute celles de
`OPTICAL_LAB_WEB_ORIGINS`. Une fois l'origine Render connue et le frontend déjà
déployé, configurer côté Vercel :

```text
VITE_API_BASE_URL=<origine réelle du service FastAPI>
```

Cette valeur est volontairement absente du dépôt. Après redéploiement du
frontend, le smoke test minimal est :

```bash
curl -fsS <origine réelle du service FastAPI>/api/v1/health
curl -fsS <origine réelle du service FastAPI>/api/v1/materials
```

La simulation n'est déclarée disponible qu'après vérification du catalogue,
de sa provenance et d'un calcul TMM depuis le frontend.

## Limites réelles

- l'importation complète dépend de la disponibilité de l'archive GitHub au build
  de l'image ; le commit reste contrôlé et aucune constante n'est fabriquée ;
- un disque persistant Render est attaché à une seule instance et impose une
  stratégie de déploiement avec interruption brève ; SQLite n'est donc pas une
  base adaptée à plusieurs instances concurrentes ;
- aucun déploiement, aucune URL et aucun secret ne sont inclus dans ce commit ;
- pour un catalogue exhaustif ou plusieurs instances, il faudra d'abord étendre
  séparément la politique d'import puis migrer vers un datastore partagé.
