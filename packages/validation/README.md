# validation
Comparaisons scientifiques Touloukian/EKHI ou CSV documentés via
`POST /api/v1/validation/compare`.

Le contrat exige une provenance de source (`source_kind`, référence et
localisateur) ainsi que, pour chaque observation, la géométrie de mesure et
les conditions connues. Seule la réflectance spéculaire directionnelle
compatible avec le TMM planaire est acceptée. Les observations hémisphériques,
l'émittance, un angle ou une polarisation différents sont refusés.

Quand aucune observation légale, traçable et comparable n'est disponible,
envoyer `observations: []` avec `unavailable_reason`. La réponse est alors
`status: "unavailable"`, sans métriques et sans prétendre à une validation.
Les données utilisateur/CSV restent marquées comme non vérifiées
indépendamment ; aucune donnée Touloukian/EKHI n'est fournie par le dépôt.
