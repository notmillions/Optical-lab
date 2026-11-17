# Architecture — Optical Lab
## Stack
- **apps/web** React + TypeScript + Vite + React Three Fiber/Three.js + Plotly
- **apps/api** FastAPI + Pydantic, API JSON versionnée
- **packages/optical_core** Fresnel, TMM, intégration spectrale, modèles de source
- **packages/material_data** ingestion YAML, dispersion, métadonnées, SQLite
- **packages/validation** métriques, références, comparaisons Touloukian/EKHI
- **data/** fixtures légères et fichiers de référence ; données volumineuses hors Git

## Frontières
`MaterialProvider` renvoie jeu de données optiques, n/k évalués aux λ autorisées, provenance et indicateurs de disponibilité. `LightSourceProvider` fournit spectres, unités et provenance. `SimulationEngine.validate(scene)` et `.run(scene)` donnent des résultats versionnés. Implémentation V1 : `PlanarTMMEngine`; V2 : `RayTracingEngine`. `VisualSceneAdapter` construit la représentation Three.js à partir de la configuration **et des résultats**, jamais en lieu et place de la physique.

## Schéma de scène exemple
```json
{
 "schema_version": "1.0", "kind": "planar-stack",
 "source": {"type": "laser", "wavelength_nm": 532, "power_W": null},
 "incidence": {"angle_deg": 30, "polarization": "s"},
 "environment": {"incident_medium": "air", "exit_medium_dataset_id": "Cu/EXAMPLE"},
 "layers": [{"id": "l1", "dataset_id": "SiO2/EXAMPLE", "thickness_nm": 100, "coherence": "coherent"}],
 "solver": "planar-tmm"
}
```
*Les identifiants EXAMPLE sont fictifs et ne devront pas être utilisés dans les données de production.*

## Modèle relationnel
`materials` → `datasets` → `samples` ou `dispersion_models`; `references` et `dataset_references`; `source_snapshots`; `radiative_measurements`; `light_sources`; `scenes` → `simulation_runs`. Garder les mesures originales en lecture seule et hacher les sources.

## API cible
- `GET /api/v1/materials?q=`
- `GET /api/v1/materials/{id}/datasets`
- `GET /api/v1/light-sources`
- `POST /api/v1/simulations`
- `GET /api/v1/simulations/{id}`
- `POST /api/v1/exports`

Réponses : `solver_version`, `scene_schema_version`, `source_snapshot_sha`, `units`, `warnings`, `status`.

## Déploiement & performances
D'abord exécution locale Mac et CI GitHub. Validation API stricte ; debounce/annulation des modifications de sliders ; cache indexé par paramètres, datasets et version solveur ; pas de données brutes massives dans Git. Work peut utiliser un checkout distinct et livrer des PR. Ne pas supposer d'accès direct au Mac depuis un environnement cloud.
