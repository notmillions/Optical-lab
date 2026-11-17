# Roadmap Optical Lab
| Phase | Domaine | Livraison contrôlable |
|---|---|---|
| P1 | Cadrage | PRD, ADR, science, schémas, CI documentaire |
| P2 | Extraction | Import YAML, SQLite, Cu/Al/SiO₂, sources conservées |
| P3 | Physique | Fresnel/TMM cohérente et mixte testées |
| P4 | Sources | Laser, soleil, lampe, intégration spectrale |
| P5 | Touloukian | Comparaison expérimentale documentée |
| P6 | Backend | API et contrats versionnés |
| P7 | Application web | Catalogue, éditeur, coupe R3F, graphiques |
| P8 | QA | Tests physiques, intégration, E2E, accessibilité |
| P9 | Livraison | Installation locale, résultats, rapport LaTeX/PDF |

## Jalons
**A — Scientific Core :** laser 532 nm et air/SiO₂/Cu calculés en Python avec références.
**B — Vertical Slice :** même simulation via API et UI, résultats synchronisés en coupe 3D.
**C — V1 :** trois types de sources, gestion matériaux, empilements, références, exports et validation.
**V2 :** objet optique libre, scènes 3D, moteurs de ray tracing et détecteurs.

## Principaux risques
Datasets n sans k ; plages λ incompatibles ; confusion entre énergie spectrale et géométrie d'éclairage ; Touloukian non comparable ; effets Three.js confondus avec physique ; import et requêtes volumineux. Toute phase doit produire des preuves de tests avant validation.
