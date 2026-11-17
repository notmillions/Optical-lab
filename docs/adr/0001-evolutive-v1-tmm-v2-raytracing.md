# ADR-0001 — Option C : TMM V1 puis ray tracing V2
**Date :** 2026-11-17. **Statut :** accepté.

## Contexte
Le TP exige une collecte de constantes optiques et des calculs radiatifs traçables. L'interface cible permet d'empiler des matériaux, d'y diriger un laser ou un spectre solaire/lampe et d'en visualiser la réponse. Des lentilles et objets libres nécessitent des modèles physiques différents de la TMM.

## Décision
- V1 : empilements homogènes planes parallèles, solveur Python TMM, frontend React/Three.js.
- V2 : objets 3D libres et solveur distinct de ray tracing.
- Contrats communs : `OpticalScene`, `MaterialProvider`, `LightSourceProvider`, `SimulationEngine`, `VisualSceneAdapter`.
- Les données et références sont mutualisées entre solveurs ; Three.js ne remplace pas la physique.

## Conséquences
(+) V1 vérifiable ; extension sans refonte totale des données.
(-) Deux familles de modèles à maintenir ; conversion géométrique et optique V2 à définir.
Le backend refuse explicitement une scène `free-3d` tant que le solveur V2 n'existe pas.
