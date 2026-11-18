# Optical Lab — état réel de la V1

**Mise à jour :** 2026-11-18. **Base :** `main` après PR #16.

| Jalon | Statut | Preuve actuelle | Écart restant |
|---|---|---|---|
| S0 fondations | **Done** | API, contrats, Vite/R3F, CI | aucun bloquant |
| S1 données | **Partial** | 4 datasets pilotes RefractiveIndex.INFO, hash et provenance | catalogue complet et autres formules |
| S2 physique | **Done** | Fresnel/TMM cohérente/mixte, R/T/A, absorption, 50 tests Python | validation expérimentale indépendante |
| S3 sources | **Partial** | laser, ASTM G173 global, lampe Planck documentée | lampe mesurée et géométrie angulaire |
| S4 validation | **Partial** | comparateur traçable, métriques et statut `unavailable` | mesure légale et comparable Touloukian/EKHI |
| S5 interface | **Partial** | catalogue, éditeur, appels API, R3F illustratif, courbes | E2E navigateur et revue visuelle |
| S6 QA/exports | **Partial** | sauvegarde locale, exports frontend et endpoint API JSON/CSV | Playwright, accessibilité automatisée, performance |
| S7 livraison | **Partial** | README, audit d’écart, rapport LaTeX | PDF si chaîne LaTeX disponible |

## Vérifications reproductibles

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff check apps packages tests scripts
python -m pytest -q
python scripts/check_docs.py
(cd apps/web && npm install --no-audit --no-fund && npm run typecheck && npm test && npm run build)
```

Dernière vérification locale : Ruff OK, 50 tests Python passés, documentation OK, TypeScript OK, 14 tests Vitest passés et build Vite OK.

## Limites non contournées

- Aucun `k` manquant n’est remplacé par zéro et aucune extrapolation n’est silencieuse.
- Les observations Touloukian/EKHI doivent être importées par l’utilisateur avec licence, géométrie, température, polarisation et surface documentées ; sinon le résultat reste `unavailable`.
- `T` est le flux entrant dans le substrat semi-infini, pas une transmission à travers sa face arrière.
- Three.js reste une illustration pilotée par les résultats TMM, pas un ray tracer.
