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
- `scripts/start_api.py` : initialise le catalogue si le fichier persistant est
  absent, puis lance Uvicorn ;
- l'initialisation réutilise l'importeur existant et son snapshot épinglé. Les
  fichiers YAML sources sont téléchargés directement puis ne sont pas conservés
  dans le conteneur.

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

Au premier démarrage, le service télécharge les quatre enregistrements déjà
approuvés par l'importeur actuel depuis le snapshot RefractiveIndex.INFO épinglé,
les écrit dans la SQLite persistante, puis démarre l'API. Les redémarrages
ultérieurs réutilisent la base existante et ne téléchargent pas à nouveau les
sources.

## Initialisation manuelle ou réparation contrôlée

Pour initialiser une base locale ou une base montée sur un shell du service :

```bash
export OPTICAL_LAB_DB=/var/lib/optical-lab/optical-lab.sqlite
python -m packages.material_data --db "$OPTICAL_LAB_DB"
```

La commande utilise le même snapshot et les mêmes contrôles de checksum que le
bootstrap automatique. Elle doit être exécutée sur le service qui possède le
disque : le disque Render n'est accessible ni au build ni à un job séparé.

La base n'est pas committée dans Git. Ne pas utiliser `data/processed/` en
production et ne pas copier un fichier SQLite dans l'image Docker : ces chemins
font partie du système de fichiers éphémère de build/runtime.

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

- le bootstrap initialise le catalogue actuellement autorisé par l'importeur,
  soit quatre datasets épinglés ; il ne transforme pas cet importeur en
  catalogue exhaustif ;
- un disque persistant Render est attaché à une seule instance et impose une
  stratégie de déploiement avec interruption brève ; SQLite n'est donc pas une
  base adaptée à plusieurs instances concurrentes ;
- aucun déploiement, aucune URL et aucun secret ne sont inclus dans ce commit ;
- pour un catalogue exhaustif ou plusieurs instances, il faudra d'abord étendre
  séparément la politique d'import puis migrer vers un datastore partagé.
