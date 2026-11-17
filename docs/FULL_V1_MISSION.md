# Optical Lab — Mission de construction intégrale V1
**Date :** 2026-11-18. **Décision :** construire toute la V1 sans arrêt volontaire après S0/S1/S2. **État initial :** dépôt documentaire ; aucune application livrée.
**Lecture préalable obligatoire :** `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/SCIENTIFIC_METHOD.md`, `docs/ROADMAP.md`, `docs/SPRINTS.md`, `docs/BACKLOG.md`, `docs/TEST_PLAN.md`, `docs/DATA_GOVERNANCE.md`, ADR option C et `docs/AUTONOMOUS_PLAN.md`.

## Mission
Livrer une V1 exécutable et démontrable : l'utilisateur sélectionne une source laser/soleil/lampe, choisit matériaux et références scientifiques, empile des couches planes, modifie les épaisseurs, la polarisation, l'angle et le spectre ; obtient de véritables résultats optiques TMM R/T/A, visualisations spectrales et vue 3D synchronisée ; peut inspecter provenance et exporter les résultats. Aucun simulateur factice.

## Contraintes fermes
1. **V1 = empilements planaires TMM ; V2 = objets 3D libres / ray tracing.** Ne pas élargir au ray tracing 3D cette nuit.
2. **Three.js/R3F uniquement pour visualiser** une coupe/empilement et les flux dérivés du solveur Python ; ne jamais prétendre que le PBR calcule la physique.
3. **Sources scientifiques réelles**. Références par dataset, domaine λ, provenance, condition de mesure si connue ; pas de valeurs n,k fictives, de k manquant substitué arbitrairement, ni d'extrapolation silencieuse.
4. **Pas de scans ni de contenu sous droits Touloukian** commité dans le dépôt public. Si la validation Touloukian/EKHI ne peut être obtenue légalement et dans les limites de l'environnement, implémenter le comparateur et documenter le blocage, sans fabriquer des données.
5. **Gestion physique honnête** : monochromatique et sources polychromatiques, intensité vs puissance absolue, domaine commun de calcul, coefficient R+T+A, incidence s/p, conditions de validité de Fresnel/TMM. Rapporter explicitement les hypothèses (plan, homogène, isotrope, linéaire, sans diffusion).
6. **Privilégier une application intégrée** plutôt que des écrans vides ou des dizaines de stubs. Les fonctionnalités P0 doivent fonctionner de bout en bout.
7. **Aucune validation fictive** : tests, builds et résultats doivent être réellement exécutés ; ne pas cocher un jalon si impossible à vérifier.

## Stack cible
- Monorepo `apps/web` React + TypeScript + Vite + React Three Fiber / Three.js + courbes Plotly, gestion d'état adaptée.
- `apps/api` Python FastAPI/Pydantic.
- `packages/optical_core` moteur scientifique Python avec NumPy, tmm, validation de cohérence ; `packages/material_data` import YAML, SQLite, références et requêtes ; `packages/validation` expérimentation.
- CI GitHub ; Pytest, Vitest, tests E2E Playwright si environnement supporté.
- CLI/scripts de démarrage local reproductible ; README à jour.
Choisir versions stables compatibles à la date d'exécution, vérifier les commandes d'installation réellement utilisées.

## Parcours de démonstration obligatoire
1. Ouvrir le catalogue et sélectionner un jeu réel de SiO₂ puis un jeu réel de Cu (avec référence et domaine λ affichés).
2. Choisir un laser idéal 532 nm, `s` puis `p`, incidence à 30°.
3. Construire air → SiO₂ (100 nm modifiable) → Cu substrat semi-infini ; sélectionner explicitement les bons datasets.
4. Calculer R, T et A avec moteur TMM, puis modifier l'épaisseur et voir un changement vérifiable dans les résultats et la coupe 3D.
5. Afficher des courbes R/T/A sur domaine spectral valide.
6. Sélectionner soleil puis lampe et obtenir des grandeurs spectralement pondérées avec origine et unités du spectre.
7. Consulter les références et télécharger/exporter un résultat CSV/JSON avec paramètres, version du solveur et provenance.
8. Consulter un écran de comparaison Touloukian/EKHI si des observations comparables sont disponibles ; sinon afficher honnêtement la limitation.

## Critères d'acceptation
- `R(n=1.5,k=0, air, 0°)=0.04` ; même réflectance pour s et p à incidence normale ; `alpha=4*pi*k/lambda_m`.
- Bilan énergétique `R+T+A≈1` dans les cas où le modèle s'applique, avec tolérance documentée et traitement des couches absorbantes.
- TMM testée sur une couche simple contre référence analytique ou bibliothèque vérifiée.
- Les coefficients spectraux proviennent de datasets explicitement choisis et restent dans leurs plages de validité.
- UI capable de configurer, simuler, comparer et exporter sans écrire du code.
- Un utilisateur tiers peut installer et démarrer backend/frontend selon README sans dépendre de fichiers secrets locaux.
- Toutes les tâches bloquées sont décrites dans `docs/EXECUTION_STATUS.md` avec commandes de tests, logs pertinents, limitations et prochaine action.

## Livraison Git
Travailler dans une branche dédiée (`feat/full-v1-overnight` ou sous-branches orchestrées), commiter par jalon et pousser. Ouvrir **une PR principale vers main sans merger** ; mettre preuves de builds/tests et éléments non terminés. Ne pas contourner la protection de branche ni demander des secrets. Mettre à jour les statuts d'issues existantes sans les clore sans preuves.

**Important :** une invocation Cloud doit être lancée explicitement par l'utilisateur. Ce document n'est pas un déclencheur automatique.
