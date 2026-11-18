# Optical Lab — Journal d'exécution autonome

**Mise à jour :** 2026-11-18. **Branche :** `feat/S0-foundations`. **PR :** https://github.com/notmillions/Optical-lab/pull/10 (draft, non fusionnée).

| Jalon | Statut | Preuve |
|---|---|---|
| M0 — S0 technique | **Implémenté et CI verte sur le commit initial S0** | API, contrats, shell React/R3F, tests API et frontend, workflow CI |
| M1 — S1 données | Non commencé | Cu/Al/SiO₂ sourcés et requêtables |
| M2 — S2 moteur TMM | Non commencé | résultats et tests analytiques |
| M3 — S3 sources | Non commencé | laser, soleil, lampe physiquement modélisés |
| M4 — S4 validation/API | Partiel : contrat API S0 seulement | API de calcul et validation Touloukian à faire |
| M5 — S5 interface 3D | Partiel : scène de prévisualisation uniquement | parcours complet réel à faire |
| M6 — S6 QA/exports | Non commencé | tests E2E, import/export |
| M7 — S7 livraison | Non commencé | rapport, docs, PR finale |

## Vérification automatisée S0

GitHub Actions `Optical Lab S0 CI` : https://github.com/notmillions/Optical-lab/actions/runs/44199765982

- Job `python` : **success** — installation, `ruff check apps packages tests`, `pytest -q`, contrôle de présence documentaire.
- Job `web` : **success** — `npm install`, `npm run typecheck`, `npm test`, `npm run build`.
- Workflow `Documentation check` : succès (GitHub Actions).
- Aucun test physique, import réel n/k ou calcul TMM n'est encore effectué. Le rendu Three.js ne fournit **aucune** réflectance, transmittance ou absorptance.
- Le service et le navigateur n'ont pas fait l'objet d'une revue visuelle humaine à ce stade ; les tests CI attestent uniquement les étapes mentionnées.

## Reprise dans Codex Cloud

Consulter la PR #10, éviter toute seconde initialisation indépendante de S0. Poursuivre sur la branche ou la fusionner après revue, puis suivre `docs/AUTONOMOUS_PLAN.md` à M1/S1, en fournissant les preuves de chacun des jalons. Ne pas fusionner les PR sans revue de l'utilisateur.
