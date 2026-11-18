# S4 — Comparaison avec les mesures expérimentales

## Statut

Le comparateur scientifique est implémenté dans `packages/validation/comparison.py`
et exposé via `POST /api/v1/validation/compare`. **Aucune table
Touloukian/EKHI authentifiée n'a été importée.** La fonctionnalité ne
constitue donc pas, à elle seule, une validation expérimentale.

## Méthode

Chaque observation est explicitement documentée : longueur d'onde (nm),
réflectance observée (fraction 0–1), angle en degrés, polarisation,
type de mesure, référence bibliographique, localisateur de la valeur,
conditions expérimentales, incertitude absolue facultative, géométrie de
l'échantillon et du détecteur. La requête porte aussi une provenance de
source (`touloukian`, `ekhi` ou `csv`) indépendante des points.

L'application n'autorise la comparaison que pour la réflectance
**spéculaire directionnelle** compatible avec le modèle TMM plan.
Les mesures hémisphériques, les émittances, les observations à angle
différent ou à polarisation incompatible sont refusées.

On calcule :

```text
residual_i = R_TMM(lambda_i) - R_observe(lambda_i)
MAE  = moyenne(|residual_i|)
RMSE = racine(moyenne(residual_i²))
```

Ces métriques ne rendent pas automatiquement comparables deux
échantillons ayant des rugosités, préparations de surface ou
températures différentes.

Si aucune mesure légale et comparable n'est disponible, la requête peut
porter une liste `observations` vide et un `unavailable_reason`. L'API
retourne alors `status: "unavailable"`, `metrics: null` et ne fabrique
aucun point ou résultat de validation.

## Endpoint

`POST /api/v1/validation/compare` avec :

```json
{
  "scene": {
    "schema_version": "1.0",
    "kind": "planar-stack",
    "source": {"type": "laser", "wavelength_nm": 532},
    "incidence": {"angle_deg": 30, "polarization": "s"},
    "environment": {
      "incident_medium": "air",
      "exit_medium_dataset_id": "main:Cu:nk:Johnson"
    },
    "layers": [
      {
        "id": "film",
        "dataset_id": "main:SiO2:nk:Gao",
        "thickness_nm": 100,
        "coherence": "coherent"
      }
    ],
    "solver": "planar-tmm"
  },
  "observations": [
    {
      "wavelength_nm": 532,
      "measured_r": 0.5,
      "measurement_type": "specular_reflectance",
      "angle_deg": 30,
      "polarization": "s",
      "source_reference": "EXEMPLE NON MESURÉ — NE PAS UTILISER EN VALIDATION",
      "source_locator": "exemple syntaxique uniquement",
      "observed_conditions": "Donnée fictive : syntaxe API uniquement"
    }
  ]
}
```

**Attention :** la valeur 0,5 ci-dessus est fictive et ne doit jamais
figurer comme mesure réelle dans un rapport ou des résultats.

## Démarche Touloukian / EKHI

1. Repérer les tableaux des volumes radiatifs 7/8 (9 si revêtement pertinent).
2. Vérifier la grandeur : `specular reflectance` à angle/polarisation
   définis ; ne pas confondre `directional-hemispherical` et `emittance`.
3. Relever, si la licence l'autorise, quelques observations, avec
   page, publication originale, température, état de surface,
   configuration et incertitude.
4. Construire le modèle TMM correspondant aux matériaux/épaisseurs.
5. Importer les mesures autorisées et calculer les résidus.
6. Interpréter les différences avec prudence ; ne pas présenter un
   modèle d'interface idéale comme explication d'une surface rugueuse.

Ne pas commiter des scans ou la reproduction intégrale d'ouvrages
protégés. Le statut API `user_supplied_observations_not_independently_verified`
est volontaire, et doit rester explicite.

## Tests

`python -m pytest tests/test_validation.py -q`

Les observations de test sont synthétiques et marquées comme telles.
