"""Read-only materials API backed by source-versioned SQLite ingestion."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from packages.material_data.store import (
    MissingDatasetError,
    SpectralDomainError,
    dataset_details,
    evaluate_constants,
    list_datasets,
    list_materials,
)

router = APIRouter(prefix="/api/v1", tags=["materials"])
DEFAULT_DB = Path("data/processed/optical-lab.sqlite")


def material_database() -> Path:
    return Path(os.environ.get("OPTICAL_LAB_DB", str(DEFAULT_DB)))


def _ready_db() -> Path:
    db = material_database()
    if not db.is_file():
        raise HTTPException(
            status_code=503,
            detail="Material database not initialized. Run python -m packages.material_data",
        )
    return db


@router.get("/materials")
def materials(q: str = Query(default="", max_length=100)) -> list[dict]:
    return list_materials(_ready_db(), q)


@router.get("/materials/catalog")
def material_catalog() -> dict[str, list[dict]]:
    """Return every material and its datasets in one grouped response."""
    database = _ready_db()
    material_rows = list_materials(database)
    datasets_by_material: dict[str, list[dict]] = {row["id"]: [] for row in material_rows}
    for dataset in list_datasets(database):
        datasets_by_material.setdefault(dataset["material_id"], []).append(dataset)
    return {
        "materials": [
            {
                **material,
                "datasets": datasets_by_material[material["id"]],
            }
            for material in material_rows
        ]
    }


@router.get("/materials/{material_id:path}/datasets")
def datasets(material_id: str) -> list[dict]:
    rows = list_datasets(_ready_db(), material_id)
    if not rows:
        raise HTTPException(status_code=404, detail="No imported datasets for this material")
    return rows


@router.get("/datasets/{dataset_id:path}/evaluate")
def evaluate_dataset(
    dataset_id: str,
    wavelength_nm: float = Query(gt=0),
    require_nk: bool = False,
) -> dict:
    try:
        return evaluate_constants(
            _ready_db(), dataset_id, wavelength_nm, require_nk=require_nk
        )
    except MissingDatasetError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc
    except SpectralDomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/datasets/{dataset_id:path}")
def get_dataset(dataset_id: str) -> dict:
    try:
        return dataset_details(_ready_db(), dataset_id)
    except MissingDatasetError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc
