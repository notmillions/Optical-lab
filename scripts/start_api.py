"""Initialize the complete persistent material catalogue, then start FastAPI.

The Docker image contains the extracted, pinned RefractiveIndex.INFO snapshot
under ``OPTICAL_LAB_SOURCE_ROOT``. The source tree is scanned only when the
persistent SQLite database has not yet been bootstrapped for that snapshot.
Every source outcome, including unsupported and invalid files, is retained in
the SQLite source manifest by :func:`packages.material_data.importer.import_catalog`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import uvicorn

from packages.material_data.importer import SNAPSHOT, import_catalog
from packages.material_data.store import list_datasets, list_source_records

DEFAULT_DATABASE = Path("/var/lib/optical-lab/optical-lab.sqlite")
DEFAULT_SOURCE_ROOT = Path("/opt/refractiveindex.info-database")
MARKER_FILENAME = "catalog-bootstrap.json"
MARKER_VERSION = 1


def _marker_path(database: Path) -> Path:
    return database.with_name(MARKER_FILENAME)


def _ready_count(database: Path, marker: Path, source_root: Path) -> int | None:
    """Return the imported dataset count only for a verified bootstrap marker."""
    if not database.is_file() or not marker.is_file():
        return None
    try:
        payload: dict[str, Any] = json.loads(marker.read_text(encoding="utf-8"))
        if (
            payload.get("version") != MARKER_VERSION
            or payload.get("snapshot") != SNAPSHOT
            or payload.get("source_root") != str(source_root)
        ):
            return None
        datasets = list_datasets(database)
        source_records = list_source_records(database)
        if (
            len(datasets) != payload.get("datasets")
            or len(source_records) != payload.get("discovered_files")
        ):
            return None
    except (OSError, TypeError, ValueError, KeyError, RuntimeError):
        return None
    return len(datasets)


def _write_marker(marker: Path, source_root: Path, *, datasets: int, discovered_files: int) -> None:
    """Publish bootstrap state atomically after the SQLite transaction commits."""
    marker.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": MARKER_VERSION,
        "snapshot": SNAPSHOT,
        "source_root": str(source_root),
        "datasets": datasets,
        "discovered_files": discovered_files,
    }
    temporary = marker.with_name(f".{marker.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(marker)


def ensure_catalogue(
    database: Path,
    *,
    source_root: Path,
    marker: Path | None = None,
) -> int:
    """Import the complete pinned catalogue once and reuse it on restart.

    A non-empty database without our marker is deliberately not considered
    ready: this upgrades the four-record pilot database left by older images.
    """
    database = Path(database)
    source_root = Path(source_root)
    marker = Path(marker) if marker is not None else _marker_path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    ready = _ready_count(database, marker, source_root)
    if ready is not None:
        return ready
    if not source_root.is_dir():
        raise RuntimeError(
            "Pinned full material snapshot is missing at "
            f"{source_root}; set OPTICAL_LAB_SOURCE_ROOT to an extracted snapshot"
        )

    report = import_catalog(database, source_root, snapshot=SNAPSHOT)
    if report.discovered_files == 0 or report.importable_datasets == 0:
        raise RuntimeError("Pinned material catalogue import produced no datasets")
    _write_marker(
        marker,
        source_root,
        datasets=report.importable_datasets,
        discovered_files=report.discovered_files,
    )
    return report.importable_datasets


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


def main() -> None:
    database = _env_path("OPTICAL_LAB_DB", DEFAULT_DATABASE)
    source_root = _env_path("OPTICAL_LAB_SOURCE_ROOT", DEFAULT_SOURCE_ROOT)
    marker = _env_path("OPTICAL_LAB_CATALOG_MARKER", _marker_path(database))
    count = ensure_catalogue(database, source_root=source_root, marker=marker)
    print(f"Material catalogue ready: {count} datasets in {database}", flush=True)
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
