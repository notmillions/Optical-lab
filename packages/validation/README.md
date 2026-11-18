# validation
Comparaisons scientifiques Touloukian/EKHI ou CSV documentés via
`POST /api/v1/validation/compare` ou `POST /api/v1/validation/compare-csv`.

Le contrat exige une provenance de source (`source_kind`, référence et
localisateur) ainsi que, pour chaque observation, la géométrie de mesure et
les conditions connues. Un CSV doit aussi fournir le SHA-256 exact du contenu
et le numéro de ligne de chaque observation. Seule la réflectance spéculaire
directionnelle d'un empilement plan, à surface non rugueuse, avec substrat
semi-infini et détecteur directionnel est acceptée. Les observations
hémisphériques, l'émittance, un angle ou une polarisation différents sont refusés.

Quand aucune observation légale, traçable et comparable n'est disponible,
envoyer `observations: []` avec `unavailable_reason`. La réponse est alors
`status: "unavailable"`, sans métriques et sans prétendre à une validation.
Les données utilisateur/CSV restent marquées comme non vérifiées
indépendamment ; aucune donnée Touloukian/EKHI n'est fournie par le dépôt.

Pour un CSV, envoyer un corps JSON avec `scene`, `source_reference`,
`source_locator` et `csv_content`. Les colonnes de métadonnées obligatoires
sont documentées dans `docs/S4_VALIDATION.md`. La réponse conserve le
SHA-256 du fichier, les colonnes reçues, le nombre de lignes et le localisateur
de chaque observation sous la forme `source_locator#row=N`. Les observations
CSV normalisées exigent également `source_sha256` et `source_row`.

Procédure reproductible : conserver le CSV original, calculer son SHA-256,
envoyer son contenu UTF-8 avec un localisateur stable, archiver la requête et
la réponse avec le commit du dépôt, puis traiter MAE/RMSE comme une comparaison
numérique non vérifiée. Un CSV vide reste `unavailable` ; aucune mesure n'est
fabriquée pour remplir le résultat.
