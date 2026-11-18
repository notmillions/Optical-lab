"""Scientific comparison API: supplied observations are never treated as verified."""

from fastapi import APIRouter, HTTPException

from apps.api.materials import _ready_db
from packages.material_data.store import MissingDatasetError, SpectralDomainError
from packages.validation.comparison import (
    ComparisonRequest,
    CsvComparisonRequest,
    compare_csv_observations,
    compare_observations,
)

router = APIRouter(prefix="/api/v1/validation", tags=["scientific validation"])


@router.post("/compare")
def compare(payload: ComparisonRequest) -> dict:
    try:
        return compare_observations(str(_ready_db()), payload)
    except MissingDatasetError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown material dataset: {exc}") from exc
    except (SpectralDomainError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/compare-csv")
def compare_csv(payload: CsvComparisonRequest) -> dict:
    """Compare a user CSV while retaining its hash and row-level provenance."""

    try:
        return compare_csv_observations(str(_ready_db()), payload)
    except MissingDatasetError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown material dataset: {exc}") from exc
    except (SpectralDomainError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
