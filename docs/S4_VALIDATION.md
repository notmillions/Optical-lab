# S4 — Comparaison avec les mesures expérimentales

## Statut

Le comparateur scientifique est implémenté dans `packages/validation/comparison.py`
et exposé via `POST /api/v1/validation/compare` et
`POST /api/v1/validation/compare-csv`. **Aucune table
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

Avant le calcul, les observations sont également contrôlées pour éviter
de mélanger des essais incompatibles : même géométrie et mêmes conditions
sur toute la série, atmosphère identique au milieu incident de la scène,
détecteur spéculaire directionnel ou angle-résolu, surface non déclarée
rugueuse/diffuse, et substrat identifié identique au milieu de sortie si
un `substrate_dataset_id` est fourni. Une surface rugueuse ou diffuse
nécessite un modèle direct différent et est donc refusée, pas corrigée
silencieusement.

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

Toutes les observations CSV sont marquées par
`verification_status: "user_supplied_observations_not_independently_verified"`.
Un CSV vide retourne `status: "unavailable"` et
`verification_status: "no_comparable_observations_available"`.

## Endpoint

### JSON normalisé

`POST /api/v1/validation/compare` accepte les observations déjà normalisées.
Pour une source CSV, `source_sha256` et `source_row` sont obligatoires afin
de conserver un lien vérifiable vers le fichier et la ligne d'origine.

### CSV utilisateur

`POST /api/v1/validation/compare-csv` accepte un corps JSON contenant
`scene`, `source_reference`, `source_locator` et `csv_content`. Le CSV doit
contenir au minimum les colonnes suivantes :

```text
wavelength_nm, measured_r, measurement_type, angle_deg, polarization,
observed_conditions, sample_description, surface_finish, surface_finish_class,
substrate_description, substrate_model, detector_geometry, detector_geometry_class,
sample_model, temperature_k, atmosphere, preparation
```

Les colonnes facultatives sont `uncertainty_absolute`, `uncertainty_method` et
`substrate_dataset_id`. Les classes de géométrie sont obligatoires afin
d'empêcher qu'une géométrie ambiguë contourne les contrôles ; une valeur
manquante n'est jamais inventée et une géométrie incompatible est refusée. La réponse
conserve l'empreinte SHA-256 du
contenu UTF-8, les colonnes reçues, le nombre de lignes et un `source_locator`
suffixé par `#row=N` dans chaque point.

Procédure reproductible :

1. Conserver le fichier CSV original sans le modifier et calculer son SHA-256.
2. Vérifier que chaque ligne décrit la même géométrie, le même angle,
   la même polarisation et les mêmes conditions.
3. Envoyer le contenu UTF-8 à `compare-csv` avec une référence bibliographique
   et un localisateur stable (nom de fichier, DOI ou page si autorisé).
4. Archiver la requête, la réponse, le SHA-256 et la version du dépôt.
5. Interpréter MAE/RMSE comme une comparaison numérique non vérifiée, jamais
   comme une validation Touloukian/EKHI automatique.

Exemple de forme de requête, sans mesure :

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
  "source_reference": "Référence bibliographique ou identifiant du fichier",
  "source_locator": "localisateur stable",
  "csv_content": "CSV UTF-8 conforme au schéma documenté"
}
```

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
