"""Initialize the persistent material catalogue, then start FastAPI.

The database is created only under OPTICAL_LAB_DB. The source YAML files are
fetched directly from the pinned RefractiveIndex.INFO snapshot by the existing
importer and are not stored in the container filesystem. A persistent volume
must therefore be mounted at the parent directory of OPTICAL_LAB_DB.
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from packages.material_data.importer import import_pilots
from packages.material_data.store import list_datasets


def ensure_catalogue(database: Path) -> int:
    """Ensure the current approved catalogue exists on persistent storage."""
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.is_file():
        datasets = list_datasets(database)
        if datasets:
            return len(datasets)

    imported = import_pilots(database, cache_dir=None)
    if imported == 0:
        raise RuntimeError("Pinned material catalogue import produced no datasets")
    return imported


def main() -> None:
    database = Path(os.environ.get("OPTICAL_LAB_DB", "/var/lib/optical-lab/optical-lab.sqlite"))
    count = ensure_catalogue(database)
    print(f"Material catalogue ready: {count} datasets in {database}", flush=True)
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
