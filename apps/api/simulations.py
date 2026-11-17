"""Scientific simulation endpoints for the Optical Lab pilot stack."""

from __future__ import annotations

from dataclasses import asdict
from math import isfinite

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from apps.api.materials import _ready_db
from apps.api.models import OpticalScene
from packages.material_data.store import MissingDatasetError, SpectralDomainError
from packages.optical_core.solver import scan_spectrum, simulate_laser

router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene: OpticalScene


class ScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    scene: OpticalScene
    wavelengths_nm: list[float] = Field(min_length=1, max_length=2000)


def _run(scene: OpticalScene, wavelengths: list[float] | None = None) -> dict:
    if scene.source.type != "laser":
        raise HTTPException(
            422, detail="S2 currently implements laser only; solar and lamps require S3"
        )
    if wavelengths is not None and any(not isfinite(w) or w <= 0 for w in wavelengths):
        raise HTTPException(422, detail="Wavelengths must be positive and finite")
    try:
        db = str(_ready_db())
        points = (
            [simulate_laser(db, scene)]
            if wavelengths is None else scan_spectrum(db, scene, wavelengths)
        )
    except MissingDatasetError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown optical dataset: {exc}") from exc
    except (SpectralDomainError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "scene_schema_version": scene.schema_version,
        "solver": "tmm",
        "status": "computed",
        "source": scene.source.model_dump(),
        "incidence": scene.incidence.model_dump(),
        "layers": [layer.model_dump() for layer in scene.layers],
        "exit_dataset": scene.environment.exit_medium_dataset_id,
        "units": {"wavelength": "nm", "R": "fraction", "T": "fraction", "A": "fraction"},
        "points": [asdict(point) for point in points],
        "note": (
            "A is absorption in finite layers; T is energy transmitted into the "
            "semi-infinite exit medium, not through its far side."
        ),
    }


@router.post("")
def calculate(payload: SimulationRequest) -> dict:
    return _run(payload.scene)


@router.post("/spectral")
def calculate_spectral(payload: ScanRequest) -> dict:
    return _run(payload.scene, payload.wavelengths_nm)
