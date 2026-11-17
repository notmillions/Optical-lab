# AGENTS.md — Instructions de travail
## Priorité
Consulter `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/SCIENTIFIC_METHOD.md`, `docs/ROADMAP.md`, `docs/SPRINTS.md` avant de développer.

## Méthode
- Travail par sprint et issue ; branches `feat/Sx-short-name`, PR avec preuve de tests.
- Respecter l'Option C : TMM V1, ray tracing libre V2.
- Ne jamais confondre shaders Three.js avec résultats physiques.
- Pas de constante optique inventée ; pas de k=0 par défaut si k est absent ; pas d'extrapolation spectrale tacite.
- Garder auteurs, DOI, source originale, plage λ, version/dataset sur tout résultat.
- Tests analytiques avant une nouvelle fonctionnalité du solveur.
- Ne pas publier des extraits/scans de Touloukian sous droits ni données propriétaires.
- Pas de secrets en dépôt. Ne pas écraser des modifications humaines ; inspecter les diffs.
- Chaque PR : résumé, tests exécutés, limites et mise à jour documentaire.
