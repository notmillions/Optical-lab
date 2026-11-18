# Sprint S1 — Import des constantes optiques

## Statut
Importateur Python et API de consultation développés sur une branche indépendante. Le périmètre pilote est **Cu Johnson, Al Rakić, SiO₂ Malitson et SiO₂ Gao**, depuis un snapshot officiel épinglé. L’import du catalogue complet se fait désormais depuis une extraction locale et produit un rapport de couverture; ne pas confondre les quatre fichiers déjà présents avec la mesure du catalogue complet. Voir [S1_CATALOG_COVERAGE.md](S1_CATALOG_COVERAGE.md).

## Source et traçabilité
Dépôt officiel : https://github.com/polyanskiy/refractiveindex.info-database

Snapshot fixé : `e6d15e364f70de1cad8a96a20f75689f2fba8b21` (7 novembre 2026).

Chemins :
- `database/data/main/Cu/nk/Johnson.yml`
- `database/data/main/Al/nk/Rakic.yml`
- `database/data/main/SiO2/nk/Malitson.yml`
- `database/data/main/SiO2/nk/Gao.yml`

Les fichiers YAML sont accessibles sous CC0 selon leur dépôt. Les références scientifiques originales restent visibles. Le stockage conserve le hash SHA-256 de chaque fichier, le commit source, les DOI éventuels, les conditions documentées et l'intervalle spectral, sans réécrire les données sources.

## Import en ligne (une fois)
Depuis la racine du monorepo, après installation de `pip install -e '.[dev]'` :

```bash
python -m packages.material_data --db data/processed/optical-lab.sqlite
python scripts/verify_s1_pilots.py
```

Le premier appel télécharge quatre YAML à une révision précise et les conserve dans `data/raw/refractiveindex-info/` (ignoré par Git). La base SQLite est dans `data/processed/` (également ignorée).

Pour réimporter sans réseau après un téléchargement réussi :

```bash
python -m packages.material_data --db data/processed/optical-lab.sqlite --offline
```

## API (après import)
Lancer le backend `python -m uvicorn apps.api.main:app --reload`.

- `GET /api/v1/materials?q=Cu`
- `GET /api/v1/materials/Cu/datasets`
- `GET /api/v1/datasets/main:Cu:nk:Johnson`
- `GET /api/v1/datasets/main:Cu:nk:Johnson/evaluate?wavelength_nm=532&require_nk=true`
- `GET /api/v1/datasets/main:SiO2:nk:Malitson/evaluate?wavelength_nm=532`

Pour Malitson, `k=null`, car sa source ne donne que `n` : c'est **une absence de donnée**, pas une absorption nulle. La série Gao est distincte et fournit `n,k` pour une couche déposée dans la plage spectrale disponible.

## Formats d'entrée pris en charge
- `tabulated nk`, `tabulated n`, `tabulated k`, avec interpolation linéaire *dans* le domaine tabulé.
- `formula 1` : Sellmeier selon la convention de RefractiveIndex.INFO, λ en µm pour l'évaluation et sorties en nm.
- Séparation des `DATA` sections et conservation des métadonnées `COMMENTS` ou `NOTES`.

Un format inconnu est rejeté explicitement par l'API stricte. Lors d'un scan du catalogue, il est conservé dans le manifeste comme section non supportée; si le fichier contient aussi des sections supportées, celles-ci restent importées avec le statut `partial`. Le moteur n'associe **jamais** n et k issus de publications différentes sans décision scientifique spécifique. Pas d'extrapolation spectrale tacite ni de fabrication de k.

## Qualité
```bash
python -m ruff check apps packages tests scripts
python -m pytest -q
python scripts/verify_s1_pilots.py
```

La dernière commande réalise un vrai import depuis le snapshot officiel et vérifie n/k à 532 nm ainsi que l'absence de k chez Malitson. Les jeux `s1_synthetic_*.yml` sont **artificiels, exclusivement pour les tests** et ne sont jamais exposés comme résultats physiques.

## Limites et suite S1
- Les autres formules de dispersion restent explicitement non supportées et sont comptées dans le rapport; elles doivent être ajoutées avec des tests analytiques dédiés, sans perte de provenance.
- L'interface React S0 n'utilise pas encore l'API matériaux.
- Touloukian n'est pas une source de n/k importée en S1. Sa validation relève de la phase scientifique suivante.
- Les données réelles sont téléchargées à la demande. Les pipelines CI réseau peuvent échouer en cas d'indisponibilité de la source ; documenter le cas au lieu de remplacer les valeurs par des constantes inventées.
