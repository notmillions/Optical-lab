# Optical Lab — Plan autonome long horizon (S0 à S7)
**But : V1 complète**, pas une preuve de concept isolée. Utiliser le cycle : inspecter → implémenter → tester → corriger → commiter → documenter → continuer.

## M0 — Bootstrap et CI (S0)
- Initialiser `apps/web` et `apps/api`, paquets Python isolés avec packaging clair, dépendances épinglées ou contraintes validées.
- Définir modèles partagés : `OpticalScene`, `MaterialDataset`, `LightSource`, `SimulationResult`, identifiants stables, validations Pydantic/TS.
- Créer une UI-shell lisible, à ce stade sans valeurs optiques inventées.
- CI : installer et lancer au moins check documentaire + tests backend + typecheck/build frontend au fur et à mesure.
**Gate :** installation, tests de démarrage et builds verts. Si échec, réparer avant M1.

## M1 — Données optiques (S1)
- Récupérer snapshot connu du dépôt officiel RefractiveIndex.INFO et conserver ref SHA/version des sources utilisées.
- Parser la structure YAML réelle, gérer tabulated n/k/nk et formules de dispersion effectivement nécessaires pour Cu, Al, SiO₂ ; si des types supplémentaires restent non supportés, les marquer et les exclure proprement.
- Ne pas confondre valeurs tabulées et valeurs calculées ; conserver provenance, auteurs, DOI, domaine, type et conditions connues.
- Stocker SQLite, fournir migration/init, recherche et évaluation spectrale avec garde-fou sur les domaines, tester Cu/Al/SiO₂.
- Ne pas commiter des jeux volumineux arbitraires.
**Gate :** au moins un dataset approprié par matériau pilote, extraction numérique reproductible, aucun k inventé, API/CLI interrogable.

## M2 — Physique (S2)
- Implémenter Fresnel s/p, absorption, coefficient `alpha`, incidence, polarisation et convention complexe.
- Adapter la bibliothèque `tmm` aux milieux incident/sortie, couches finies, substrats semi-infinis et cas de cohérence supportés. La TMM a ses propres conventions : les vérifier explicitement.
- Simuler un laser à 532 nm dans un empilement air/SiO₂/Cu avec références valides. Ajouter balayage spectral et bilan d'énergie.
- Tests analytiques et comparaison indépendante.
**Gate :** vrais R/T/A, tests de référence et cas limites verts.

## M3 — Sources (S3)
- Laser monochromatique paramétrable, angle/polarisation.
- Soleil : spectre de référence validé (par ex. ASTM G173 selon droits et disponibilité) et origine explicite.
- Lampe : spectre représentatif documenté ou import CSV réellement pris en charge ; pas de pseudo-courbe arbitraire non identifiée.
- Intégration spectrale pondérée sur support commun et résultat sous forme de coefficients, non de watts sans puissance d'entrée/conditions définies.
**Gate :** source sélectionnable ; validation des unités et de la gamme spectrale.

## M4 — API, exploitation Touloukian (S4)
- API FastAPI JSON : GET matériaux/datasets, GET sources, POST simulation, export ; validation stricte et erreurs d'entrée explicites.
- Identifier, si accessible légalement, des séries des volumes radiatifs Touloukian 7/8/9 ou EKHI ; importer et comparer seulement des grandeurs équivalentes.
- Si unavailable/under rights : livrer comparateur de mesures documentées/import CSV, procédure reproductible et état « validation expérimentale non disponible », sans usurper la validation.
**Gate :** même résultat en Python et API ; comparaison honnête et sourcée quand possible.

## M5 — Optical Studio (S5)
- Catalogue et fiche matériau : recherche, n/k, references, domaine λ.
- Source selector : laser, soleil, lampe.
- Layer editor : ajouter/supprimer/réordonner, épaisseurs nm/µm, incident et substrat.
- Simulateur : angle, polarisation, grille λ, états d'erreur, affichage de R/T/A.
- Scène R3F interactive : coupe des couches, zoom, représentation de flux calculés ; ne pas faire croire que les chemins de rayons sont réellement simulés par Three.js.
- Graphiques spectraux, énergies pondérées, légendes et unités.
**Gate :** scénario de démo en UI complet, pas seulement un wireframe.

## M6 — Résilience, QA et exports (S6)
- Sauvegarder/recharger scènes versionnées, export CSV et JSON avec provenance/versions.
- Pytest data/physique/API, Vitest UI, Playwright E2E si support, lint, typecheck, build prod ; tests accessibilité et états de chargement.
- Caching et requêtes annulables pour les sliders, contrôles de performance.
- Tests de comparaison n/k et de non-extrapolation ; signaler les trous spectraux.
**Gate :** scénario complet fonctionne après lancement à froid, erreurs explicites et non masquées.

## M7 — Livraison et revue (S7)
- README installation reproductible, architecture mise à jour, commandes de lancement, guide utilisateur et limitations physiques.
- Rapport TP (source LaTeX, PDF si chaîne disponible) : objectifs, méthode acquisition, équations, jeux de données, démonstration, validations et limites. Ne pas inventer de figures ou résultats.
- Exécuter suite de tests finale, vérifier cohérence du dépôt, pousser branche, ouvrir PR principale, conserver `main` inchangée.
- Rapporter chaque jalon Done/Partial/Blocked avec preuve dans `docs/EXECUTION_STATUS.md` et la PR.
**Gate final :** réponse API + frontend + moteur avec vrais résultats et preuves. Ne jamais annoncer « V1 terminée » si non vérifiée.

## Règles anti-arrêt prématuré
- Ne pas terminer après S0, S1 ou S2 si les sprints suivants sont faisables.
- Ne pas demander un choix pour des détails réversibles ; choisir solution simple, documenter.
- Si internet indisponible pour des datasets, utiliser des fixtures libres et explicitement sourcées si elles existent, puis signaler que le catalogue complet est bloqué ; ne jamais inventer n/k.
- Si un jalon bloque, tenter réparation, puis travailler sur les autres jalons indépendants, consigner les limitations et faire le maximum utile dans l'exécution.
- Si la session s'arrête par limites ou quota, pousser l'état fonctionnel et documenter précisément comment la reprendre. Ne pas prétendre redémarrer automatiquement.
