"""Reproducible API exports for already-computed simulation results."""

from __future__ import annotations

import csv
import io
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict

from apps.api.models import OpticalScene

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene: OpticalScene
    result: dict
    format: Literal["json", "csv"] = "json"


@router.post("")
def export_result(payload: ExportRequest):
    bundle = {
        "export_schema_version": "1.0",
        "scene": payload.scene.model_dump(),
        "result": payload.result,
        "units": payload.result.get("units", {}),
        "warnings": payload.result.get("warnings", []),
        "interpretation": (
            "T is flux entering the semi-infinite exit substrate, not transmission "
            "through its rear face. A covers finite layers."
        ),
    }
    if payload.format == "json":
        return bundle
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["wavelength_nm", "polarization", "R", "T", "A", "T_interpretation"])
    for point in payload.result.get("points", []):
        writer.writerow([
            point.get("wavelength_nm"), point.get("polarization"),
            point.get("reflectance"), point.get("transmittance"), point.get("absorptance"),
            "flux into semi-infinite exit substrate; not rear-face transmission",
        ])
    return PlainTextResponse(output.getvalue(), media_type="text/csv")
