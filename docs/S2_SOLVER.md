# Sprint S2 — Fresnel et moteur multicouche TMM

## Résumé
S2 ajoute un solveur physique indépendant de la scène Three.js avec la bibliothèque scientifique [tmm](https://github.com/sbyrnes321/tmm) de Steven Byrnes. L'entrée est une scène `OpticalScene` versionnée décrivant les couches planes, leur épaisseur, leurs jeux de données source, la polarisation et l'incidence.

**La première intégration S2 traite le laser monochromatique et les balayages spectraux paramétrés ;** soleil et lampe restent à S3. L'interface Three.js reste illustrative tant qu'elle n'est pas raccordée à l'API.

## Contrats et limites scientifiques
- Convention `n_complex = n + i k`, `k >= 0` : `tmm` utilise la même convention.
- Tous les calculs d'épaisseur et de longueur d'onde sont effectués en **nm**.
- Milieu incident : air transparent d'indice 1 (pour S2) ; couches homogènes, isotropes, planes et linéaires.
- Dernière couche : **milieu de sortie semi-infini**. La transmittance `T` est le flux **entrant dans le substrat**, et non le flux qui ressort à l'arrière du substrat.
- L'absorptance `A = 1 - R - T` décrit les couches **finies**. Si le substrat semi-infini est absorbant, `T` finira éventuellement absorbé dedans, mais ne doit pas être ajouté à `A` pour un bilan `R+T+A=1`.
- Si une couche cohérente/incohérente est définie, choisir `coh_tmm` ou `inc_tmm`/les calculs d'absorption associés.
- Polarisations `s`, `p`, non polarisée (moyenne des intensités indépendantes).
- Les sources `n` seules (par exemple SiO₂/Malitson) ne suffisent pas pour une TMM avec extinction : le solveur exige un jeu contenant **n et k à la longueur d'onde demandée**, sans inventer k=0.

## API S2
```http
POST /api/v1/simulations
POST /api/v1/simulations/spectral
```

Exemple de corps de requête pour un laser 532 nm sur **SiO₂/Gao** avec **Cu/Johnson** en substrat :

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
        "id": "L1",
        "dataset_id": "main:SiO2:nk:Gao",
        "thickness_nm": 100,
        "coherence": "coherent"
      }
    ],
    "solver": "planar-tmm"
  }
}
```

Importer d'abord les jeux S1 dans SQLite :

```bash
python -m pip install -e '.[dev]'
python -m packages.material_data
python -m uvicorn apps.api.main:app --reload
```

Pour le balayage spectral, utiliser la même scène mais avec `"wavelengths_nm":[450,500,532,600]` dans le JSON transmis à `POST /api/v1/simulations/spectral`. Les longueurs d'onde doivent appartenir au domaine commun des matériaux.

## Tests
- Cas analytique Fresnel air / n=1,5, k=0 : R=0,04.
- Identité s/p à incidence normale.
- Atténuation `alpha = 4*pi*k/lambda_m`.
- Conservation R+T+A=1 pour les systèmes passifs.
- Absorption des couches finies ; cohérent / incohérent ; moyenne non polarisée.
- API : calcul mono et spectral, refus d'ID inconnus, absence du spectre lampe/soleil avant S3.
- Les tests optiques unitaires utilisent **uniquement des constantes synthétiques identifiées**, tandis que S1 continue à vérifier la récupération de véritables YAML.

## Suite
S3 : données solaires et spectres de lampes réellement sourcés, intégration spectrale pondérée. S5 : liaison UI/Three.js aux calculs (aucune donnée affichée ne doit être présentée comme mesurée tant que le backend n'a pas répondu).
