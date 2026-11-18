# S1 — couverture du catalogue RefractiveIndex.INFO

## Source et règle d’import

Le catalogue doit être extrait localement au snapshot
`e6d15e364f70de1cad8a96a20f75689f2fba8b21`. L’import ne fait pas de requête
réseau et ne fabrique aucune constante. Il parcourt uniquement :

```text
database/data/main/**/nk/*.yml
```

Un fichier YAML reste un dataset indépendant, même lorsqu’il contient
plusieurs sections `DATA`. Les sections prises en charge sont `tabulated n`,
`tabulated k`, `tabulated nk` et `formula 1`. Les autres sections sont
enregistrées comme non supportées avec leur numéro, leur type et leur motif;
elles ne sont jamais interprétées.

## Commande reproductible

```bash
python -m packages.material_data \
  --source-root /path/to/refractiveindex.info-database \
  --db data/processed/refractiveindex-info.sqlite \
  --coverage-report data/processed/refractiveindex-info-coverage.json
```

Le rapport distingue :

- `importable_datasets` : fichiers comportant au moins une section supportée;
- `fully_supported_datasets` : toutes les sections sont supportées;
- `partially_imported_datasets` : les sections supportées sont importées, les
  autres sont explicitement signalées;
- `unsupported_files` : aucune section interprétable;
- `invalid_files` : YAML ou métadonnées invalides.

La base conserve également le manifeste complet dans `source_records`, y
compris les fichiers non importables. Cela permet de mesurer la couverture
sans confondre « fichier découvert » et « matériau disponible pour le solveur ».

## État de mesure local

Le checkout de développement ne contient actuellement que les quatre YAML
pilotes sous `data/raw/refractiveindex-info/`. La commande ci-dessus doit être
relancée avec l’extraction complète pour obtenir le nombre du catalogue entier;
aucun nombre global n’est inventé à partir de ces quatre fichiers.
