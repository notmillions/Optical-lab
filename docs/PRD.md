# PRD — Optical Lab V1.0
**Statut :** Option C validée — 17/11/2026. **Type :** TP universitaire.

## Problème
Réunir des constantes optiques n(λ), k(λ) sourcées et des références expérimentales, construire des empilements de matériaux et simuler leur réponse à des sources lumineuses.

## Vision produit
L'utilisateur sélectionne une source **laser / soleil / lampe**, choisit des jeux de données propres à chaque matériau, empile des couches planes et modifie épaisseurs, angle d'incidence, polarisation. Il obtient **R(λ), T(λ), A(λ)**, des grandeurs intégrées selon le spectre et une coupe 3D illustrative.

## Exigences V1 (P0)
- **FR-01** Catalogue de matériaux avec recherches et jeux de données alternatifs.
- **FR-02** Acquisition RefractiveIndex.INFO, préservation version, DOI/auteurs, plages de validité.
- **FR-03** Sources : laser monochromatique, spectre solaire de référence, lampe mesurée ou documentée.
- **FR-04** Éditeur d'empilements : couches ordonnées, épaisseurs, substrat et milieu incident.
- **FR-05** Incidence et polarisation s/p/non polarisée, avec hypothèses explicites.
- **FR-06** Calculs spectraux R/T/A et absorption par couche lorsque applicable.
- **FR-07** TMM cohérente et couches incohérentes selon le modèle applicable.
- **FR-08** Scène 3D interactive et synchronisée avec les résultats du solveur.
- **FR-09** Graphiques, tableaux et comparaisons.
- **FR-10** Exploitation Touloukian/EKHI : au moins une validation aux conditions comparables.
- **FR-11** Exports CSV/JSON contenant configuration, versions et références.

## Exigences P1
Sauvegarde/import de scènes JSON versionnées ; import CSV de spectres personnalisés.

## Limites
V1 : couches homogènes, isotropes, linéaires, planes et parallèles, interfaces idéales ; ni rugosité/diffusion 3D ni anisotropie ou effets non linéaires. Soleil et lampes sont traités spectralement ; leur distribution angulaire ne doit pas être assimilée sans justification à un laser collimaté. Three.js est un rendu, non le solveur. Ne pas transformer k manquant en k=0 sans justification.

## V2
Objets optiques 3D libres, lentilles, prismes, miroirs, détecteurs et moteur de ray tracing indépendant de la TMM.

## Definition of Done V1
Choix source + données n/k sourcées + assemblage air/SiO₂/Cu + modification épaisseur/angle/polarisation + résultat R/T/A physiquement validé + coupe 3D + export/reproductibilité + dossier de validation Touloukian + tests automatisés.

## Questions ouvertes
Le professeur exige-t-il un scraping HTML strict plutôt qu'une ingestion YAML ? Licence du code à sélectionner. Droit de réutilisation des contenus Touloukian/EKHI à qualifier avant export.
