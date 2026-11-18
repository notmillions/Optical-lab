# Audit QA indépendant — catalogue, API séparée et Vercel

**Date :** 2026-11-18
**Périmètre :** contrôles de contrat et vérification documentaire uniquement.
**Règle scientifique :** aucune constante, mesure ou ligne de catalogue n'a été ajoutée.

## Verdict

Le dépôt est préparé pour un frontend Vercel et une API FastAPI séparée, mais il
ne fournit pas encore la preuve d'un déploiement V1 complet. L'interface seule
peut répondre alors que l'API, la base ou le catalogue sont indisponibles.

| Élément | État observé | Preuve / risque |
|---|---|---|
| Catalogue « tous matériaux » | **Non réalisé** | `packages/material_data/importer.py` ne contient que 4 chemins épinglés : Cu/Johnson, Al/Rakic, SiO₂/Malitson et SiO₂/Gao. |
| Matériaux exposés par l'UI | **Limité à 3** | `apps/web/src/lib/api.ts` demande uniquement SiO₂, Cu et Al. Ce n'est pas un catalogue complet. |
| API séparée | **Préparée, non déployée** | FastAPI est un service distinct ; aucune URL publique ni preuve de smoke test distant n'est versionnée. |
| Base de matériaux | **Locale/pilote** | SQLite est créée par import, `data/processed/` est ignoré par Git et aucune initialisation de production n'est automatisée dans le dépôt. |
| Health | **Liveness seulement** | `/api/v1/health` renvoie `200` sans vérifier SQLite ni la présence de datasets. Un `200` ne prouve donc pas que le catalogue est prêt. |
| Vercel | **Frontend préparé** | `VITE_API_BASE_URL` existe, mais aucun `.vercel/`, `vercel.json` ou identifiant de projet n'est présent. |
| CORS | **Borné par configuration** | Le backend autorise les deux origines locales et `OPTICAL_LAB_WEB_ORIGINS`; l'origine Vercel exacte doit être injectée au runtime. |
| Frontend sans API | **Risque réel** | Une valeur vide de `VITE_API_BASE_URL` conserve les routes relatives : l'UI se charge, mais un hébergement statique sans proxy ne peut pas simuler. |

## Contrats QA ajoutés

`tests/test_deployment_contracts.py` vérifie sans données optiques :

- le contrat actuel de liveness de `/api/v1/health` ;
- le `503` explicite du catalogue quand `OPTICAL_LAB_DB` ne pointe pas vers une
  base initialisée ;
- l'acceptation de l'origine locale documentée ;
- le refus d'une origine CORS arbitraire.

Ces tests ne prétendent pas vérifier une base de production, une URL Vercel ou
un réseau distant. Ils empêchent seulement de confondre les contrats locaux
avec une preuve de déploiement.

## Conditions de sortie avant annonce « V1 déployée »

1. Importer le catalogue autorisé réellement choisi, avec snapshot, hash,
   auteurs, références et domaines conservés pour chaque dataset. Tant que
   l'importeur reste limité aux quatre pilotes, annoncer « catalogue pilote ».
2. Héberger FastAPI sur un service Python 3.11+ séparé de Vercel.
3. Initialiser la base dans ce service à partir d'un artefact de données
   autorisé et persistant. Une SQLite dans un filesystem éphémère ne constitue
   pas une base de production fiable.
4. Ajouter une vérification distante de readiness qui teste au minimum le
   schéma SQLite et le nombre de datasets attendus ; le health actuel ne suffit
   pas pour ce rôle.
5. Définir dans Vercel `VITE_API_BASE_URL` avec l'origine HTTPS publique exacte
   de FastAPI, puis reconstruire le frontend. La valeur vide ne doit être
   utilisée que pour le proxy Vite local.
6. Définir `OPTICAL_LAB_WEB_ORIGINS` avec le domaine Vercel exact, sans wildcard
   ni origine de développement en production, puis vérifier une requête CORS
   réelle et une origine non autorisée.
7. Exécuter sur les URLs publiques un smoke test santé → catalogue → simulation
   → export, en vérifiant aussi la provenance des datasets.

## Limites de cet audit

- Aucun accès authentifié à Vercel n'a été utilisé.
- Aucun service FastAPI public, volume persistant ou artefact de catalogue de
  production n'est identifiable dans le dépôt au moment de l'audit.
- Les tests Python nécessitent l'environnement déclaré par le projet
  (`Python >= 3.11` et dépendances de `.[dev]`).
