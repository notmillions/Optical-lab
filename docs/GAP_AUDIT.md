# Audit d’écart entre le plan et le dépôt

**Date :** 2026-11-18 — **référence :** `docs/AUTONOMOUS_PLAN.md`, `docs/PRD.md`, `main` après PR #16.

| Domaine | Implémenté | Écart vérifiable | Action |
|---|---|---|---|
| M0/S0 | contrats, CI, UI shell | aucun critique | statut mis à jour |
| M1/S1 | parser YAML, SQLite, 4 pilotes, provenance | catalogue élargi | backlog, sans données inventées |
| M2/S2 | Fresnel, TMM, absorption, tests | validation externe | comparateur S4 sans claim de validation |
| M3/S3 | laser, ASTM G173, Planck documenté | lampe mesurée, angles solaires | hypothèses explicites |
| M4/S4 | comparaison CSV/observations, MAE/RMSE | données Touloukian/EKHI licites | importer seulement des mesures traçables |
| M5/S5 | catalogue, couches, calcul, courbes, R3F | E2E et revue visuelle | tâche QA suivante |
| M6/S6 | sauvegarde, JSON/CSV, export API | Playwright, accessibilité/performance | tâche QA suivante |
| M7/S7 | README, état, rapport LaTeX | PDF sans outil | génération conditionnelle |

## Corrections réalisées

- Ajout de `POST /api/v1/exports` en JSON/CSV, avec unités, avertissements et sémantique du substrat semi-infini.
- Capacités API corrigées de `S1` vers `V1-partial` et exposant exports/comparaisons.
- Contrat `OpticalConstants.n` durci à `n > 0`.
- `docs/EXECUTION_STATUS.md` recalé sur `main`.

## Blocages externes

1. Mesure expérimentale Touloukian/EKHI légalement réutilisable et comparable.
2. Navigateur Playwright disponible pour l’E2E.
3. Chaîne LaTeX disponible pour produire le PDF.
