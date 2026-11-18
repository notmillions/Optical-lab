# Optical Lab — Journal d'exécution autonome

**Mise à jour :** 2026-11-18. **Base inspectée :** `origin/feat/S6-reproducible-exports` (`0c40cd9`). **Chantier :** documentation de livraison S7.

Ce document décrit l'état observé du dépôt, pas une promesse de complétude. « Done » signifie que le code et les tests correspondants sont présents dans la base inspectée; la vérification locale de cette session est indiquée séparément.

| Jalon | Statut réel au 2026-11-18 | Preuve / limite |
|---|---|---|
| M0 — S0 technique | **Partial** | Structure API/web et workflows présents; reproduction locale non installée dans cette session. |
| M1 — S1 données | **Partial** | Import épinglé et quatre datasets pilotes documentés; catalogue complet et formats supplémentaires restent hors périmètre. |
| M2 — S2 moteur TMM | **Partial** | Solveur Fresnel/TMM, absorption et endpoints présents avec tests; exécution locale bloquée par dépendances absentes. |
| M3 — S3 sources | **Partial** | Laser, ASTM G173 via pvlib et lampe Planck présents; lampe réelle et distribution angulaire solaire restent limitées. |
| M4 — S4 validation/API | **Blocked** | `packages/validation` indique que les comparaisons Touloukian/EKHI ne sont pas implémentées; aucune mesure n'est inventée. |
| M5 — S5 interface 3D | **Partial** | UI React/R3F, graphique et appels API présents; revue visuelle et E2E non attestées ici. |
| M6 — S6 QA/exports | **Partial** | Sauvegarde de scène, validation, CSV avec provenance et tests Vitest présents; exécution complète à confirmer. |
| M7 — S7 livraison | **Partial** | README, journal et rapport LaTeX ajoutés; PDF non produit, `pdflatex` absent. PR/revue non effectuées dans ce workspace. |

## Vérifications de cette session

Branche `feat/S7-delivery-documentation`, dérivée de `origin/feat/S6-reproducible-exports`.

- `python3 scripts/check_docs.py` : **réussi**.
- `python3 -m ruff check apps packages tests scripts` : **bloqué**, module `ruff` absent.
- `python3 -m pytest -q` : **bloqué à la collecte**, `fastapi` absent et l'interpréteur système est Python 3.9 alors que le projet demande Python >=3.11.
- `cd apps/web && npm run typecheck` : **bloqué**, `tsc` absent (dépendances npm non installées).
- `npm test` et `npm run build` : non exécutés après ce blocage.
- `pdflatex`, `latexmk`, `tectonic` : non disponibles; aucun PDF n'est donc déclaré ou ajouté.

## Commandes de reproduction propres

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ruff check apps packages tests scripts
python -m pytest -q
python scripts/check_docs.py
(cd apps/web && npm install && npm run typecheck && npm test && npm run build)
```

Pour les données réelles, suivre `docs/S1_INGESTION.md`, puis exécuter `python scripts/verify_s1_pilots.py` et `python scripts/verify_v1_demo.py`. Ces commandes doivent être relancées dans un environnement équipé avant de qualifier la V1 de complète.

## Limites scientifiques à conserver

- Les données synthétiques servent uniquement aux tests.
- Aucun `k` manquant n'est remplacé par zéro et aucune extrapolation silencieuse n'est autorisée.
- La validation Touloukian/EKHI reste bloquée tant qu'une mesure comparable, licite et correctement métadonnée n'est pas disponible.
- `T` est le flux entrant dans le substrat semi-infini; il ne signifie pas transmission à travers sa face arrière.
- La scène Three.js est une illustration, pas un ray tracer physique.
