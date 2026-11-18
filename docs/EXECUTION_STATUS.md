# Optical Lab — Journal d'exécution autonome

**Mise à jour :** 2026-11-18. **Branche :** `feat/S0-foundations`. **PR :** https://github.com/notmillions/Optical-lab/pull/10 (draft, non fusionnée).

| Jalon | Statut | Preuve |
|---|---|---|
| M0 — S0 technique | **Implémenté et CI verte sur le commit initial S0** | API, contrats, shell React/R3F, tests API et frontend, workflow CI |
| M1 — S1 données | **Partiellement terminé : 4 datasets pilotes réels** | Import YAML épinglé, SQLite, API, provenance, contrôle de domaine ; extension du catalogue et types supplémentaires à faire |
| M2 — S2 moteur TMM | **Prototype fonctionnel (laser, films cohérents ou mixtes)** | Solveur Python TMM et endpoint calcul/spectral ; tests Fresnel et conservation CI réussis, intégration web non faite |
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

Consulter la PR #10 et la PR S1 dédiée, éviter toute initialisation indépendante de S0. Poursuivre sur la branche ou la fusionner après revue, puis suivre `docs/AUTONOMOUS_PLAN.md` à M1/S1, en fournissant les preuves de chacun des jalons. Ne pas fusionner les PR sans revue de l'utilisateur.

## Intégration scientifique S1 (18 novembre 2026)

- Snapshot RefractiveIndex.INFO : `e6d15e364f70de1cad8a96a20f75689f2fba8b21`.
- Quatre références indépendantes : Cu/Johnson, Al/Rakic, SiO₂/Malitson (n sans k), SiO₂/Gao (n,k).
- Contrôle YAML, normalisation µm → nm, interpolation linéaire et Sellmeier formule 1, exclusions hors domaine, provenance et hashes SHA256.
- SQLite, routes API et CLI d'import avec cache/offline.
- CI verte : https://github.com/notmillions/Optical-lab/actions/runs/44202351805
  - `ruff`, `pytest`, import **réel** des quatre fichiers YAML épinglés et vérification n/k à 532 nm.
  - `npm run typecheck`, `npm test`, `npm run build` réussis.
- **Limites :** seuls les quatre jeux pilotes sont importés ; autres formules non prises en charge et catalogue complet non importé ; l'UI n'interroge pas encore le catalogue.
- Les données optiques synthétiques dans `data/fixtures/` servent uniquement aux tests, jamais aux simulations physiques.

## Mise à jour S2 — moteur TMM (18 novembre 2026)

- `packages/optical_core/solver.py` : Fresnel à incidence normale, alpha, TMM cohérente/mixte, s/p et non polarisée, absorption par couche, scan spectral.
- `apps/api/simulations.py` : calculs laser et scan via API avec erreurs scientifiques explicites.
- Les propriétés optiques proviennent des jeux S1, avec vérification de domaine et de disponibilité de k.
- Attention : `T` est la puissance **entrant dans le substrat semi-infini** ; `A=1-R-T` représente les pertes des couches finies. Le flux T peut être absorbé dans un substrat métallique semi-infini sans être une transmission au travers de sa face arrière.
- Tests scientifiques S2, API et continuité S1 vérifiés par GitHub Actions : https://github.com/notmillions/Optical-lab/actions/runs/44203491476 (succès Python + Web).
- Limites : système laser S2 uniquement ; la scène web est encore illustrative ; pas de sources solaire/lampe (S3), ni comparateur Touloukian (S4).
