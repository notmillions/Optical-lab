# Backlog priorisé
Statut recalé sur `main` après PR #16. `[x]` = implémenté et couvert par les preuves disponibles ; `[~]` = partiel ; `[ ]` = ouvert.

## S0 — Fondations
- [x] OL-001 : contrat de scène et hypothèses scientifiques
- [x] OL-002 : monorepo, Python et Vite initialisés
- [x] OL-003 : workflow CI, lint, format et tests
- [x] OL-004 : schéma de provenance et décision ADR
- [x] OL-005 : cas analytiques de référence

## S1 — Material data
- [x] OL-101 : source RefractiveIndex.INFO identifiée par commit
- [x] OL-102 : parser tabulated nk/n/k, formules de dispersion
- [x] OL-103 : schéma SQLite + initialisation
- [x] OL-104 : importer Cu, Al, SiO₂
- [x] OL-105 : règles d'interpolation/masque spectral, audit de provenance
- [~] OL-106 : import catalogue élargi, tests et métriques

## S2 — Physics
- [x] OL-201 : Fresnel s/p et incidence normale
- [x] OL-202 : adaptateur TMM couches cohérentes
- [x] OL-203 : incohérence/mixte ; absorption par couche
- [x] OL-204 : grille λ, angle, polarisation, unités
- [x] OL-205 : tests numériques, bilan énergétique

## S3 — Spectres
- [x] OL-301 : laser monochromatique
- [x] OL-302 : soleil normalisé et documentation
- [x] OL-303 : spectre de lampe documenté
- [x] OL-304 : pondération intégrale

## S4 — Références + API
- [~] OL-401 : qualification données Touloukian/EKHI
- [x] OL-402 : comparaison traçable et rapport de limites
- [x] OL-501 : endpoints matériaux, sources, simulations, exports
- [x] OL-502 : validation et tests d'intégration

## S5 — UI scientifique
- [x] OL-601 : catalogue et fiche matériau
- [x] OL-602 : éditeur ordonné de couches
- [x] OL-603 : source et commandes d'incidence
- [x] OL-604 : vue Three.js/R3F synchronisée
- [x] OL-605 : courbes R/T/A et avertissements

## S6 — Stabilisation
- [x] OL-701 : comparaison, sauvegarde et exports
- [ ] OL-702 : tests E2E, accessibilité, performances
- [x] OL-703 : contrôle scientifique transversal

## S7 — Livraison
- [x] OL-801 : guide d'installation et démonstration
- [~] OL-802 : résultats et rapport LaTeX/PDF
- [x] OL-803 : release V1 reproductible
