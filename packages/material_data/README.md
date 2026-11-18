# material_data

Import, normalisation, provenance and SQLite queries for optical properties
from a pinned RefractiveIndex.INFO snapshot.

## Full local-catalog import

The importer does not download or synthesise optical constants. Extract the
source repository at snapshot
`e6d15e364f70de1cad8a96a20f75689f2fba8b21`, then run from the monorepo root:

```bash
python -m packages.material_data \
  --source-root /path/to/refractiveindex.info-database \
  --db data/processed/refractiveindex-info.sqlite \
  --coverage-report data/processed/refractiveindex-info-coverage.json
```

The command visits exactly
`database/data/main/**/nk/*.yml`. Each YAML file is one independent dataset;
its SHA-256, source path, snapshot commit, references, DOI URLs, conditions,
sections and spectral domain are retained. The SQLite `source_records` table
also retains every scanned file, including files that could not be imported.

Supported DATA sections are:

- `tabulated n`, `tabulated k`, and `tabulated nk`;
- `formula 1` (Sellmeier, with the source wavelength range).

Unknown or unsupported sections are recorded with their ordinal, source type
and reason. A file containing supported and unsupported sections is imported
as `partial`; a file with no supported section is retained as `unsupported`
and is never exposed as a material dataset. Malformed files are `invalid`.
No missing `k` is changed to zero and no constants are copied between files.

The coverage report gives discovered files, importable datasets, fully and
partially supported datasets, unsupported/invalid files, section counts and
per-file reasons. JSON is recommended for machine checks; any other suffix
produces Markdown.

The older pilot command remains available for the four pinned smoke fixtures:

```bash
python -m packages.material_data \
  --db data/processed/s1-integration.sqlite \
  --cache-dir data/raw/refractiveindex-info
```
