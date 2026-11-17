# Plan de tests
## Scientific tests (Pytest)
- Fresnel depuis l'air : n=1.5, k=0 → R=0.04 et T=0.96 à incidence normale.
- s/p donnent la même réflectance à θ=0.
- `α=4πk/λ` avec unités contrôlées ; α=0 si k=0.
- Échantillons passifs dans le domaine du modèle : R+T+A=1 aux tolérances documentées.
- TMM couches nulles, empilement simple, dépendance à épaisseur et λ.
- Comparaison numérique à une référence analytique ou indépendante.
## Material data
- Domaines λ, NaN, unités, interpolation, séries partielles, DOI/auteurs, hash source, doublons, version de snapshot.
- Refus d'extrapolation ou d'imputation silencieuse de k.
## API / UI
- Contrats Pydantic ; erreurs scientifiques explicites ; même résultat du core et de l'API.
- Vitest composants ; Playwright parcours laser → empilement → calcul → export.
- Rendu Three.js synchronisé et balisé « illustration ».
- Accessibilité clavier, états de chargement, performances.
## CI
La CI documentaire initiale ne prouve **pas** le fonctionnement des moteurs à développer. Étendre la CI lorsque les projets Python et React existent.
