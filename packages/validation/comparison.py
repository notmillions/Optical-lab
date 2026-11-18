"""Compare physical TMM predictions with user-supplied, traceable measurements.

No Touloukian or EKHI measurements are bundled or fabricated. An observation
must describe specular reflectance at an angle and polarization compatible with
the model. Hemispherical reflectance and thermal emittance are not comparable
to the planar specular calculation without a different forward model.
"""

from __future__ import annotations

import csv
import hashlib
import io
from math import isfinite, sqrt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.api.models import OpticalScene
from packages.optical_core.solver import simulate_planar


class MeasurementGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    sample_description: str = Field(min_length=3)
    surface_finish: str = Field(min_length=3)
    surface_finish_class: Literal["smooth", "polished", "rough", "unknown"] | None = None
    substrate_description: str | None = None
    substrate_model: Literal["semi_infinite_exit_medium", "finite_substrate", "unknown"] | None = (
        None
    )
    substrate_dataset_id: str | None = Field(default=None, min_length=1)
    detector_geometry: str = Field(min_length=3)
    detector_geometry_class: (
        Literal[
            "specular_directional",
            "angle_resolved",
            "hemispherical",
            "integrating_sphere",
            "unknown",
        ]
        | None
    ) = None
    sample_model: Literal["planar_stack", "nonplanar", "unknown"] | None = None


class MeasurementConditions(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    temperature_k: float | None = Field(default=None, gt=0)
    atmosphere: str = Field(min_length=2)
    preparation: str = Field(min_length=3)
    uncertainty_method: str | None = None


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    wavelength_nm: float = Field(gt=0)
    measured_r: float = Field(ge=0, le=1)
    measurement_type: str = Field(default="specular_reflectance")
    source_kind: Literal["touloukian", "ekhi", "csv"]
    angle_deg: float = Field(ge=0, lt=90)
    polarization: str
    source_reference: str = Field(min_length=5)
    source_locator: str = Field(min_length=1)
    source_row: int | None = Field(default=None, ge=2)
    observed_conditions: str = Field(min_length=5)
    geometry: MeasurementGeometry
    conditions: MeasurementConditions
    uncertainty_absolute: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def supported_observation(self):
        if self.measurement_type != "specular_reflectance":
            raise ValueError(
                "Only specular_reflectance is supported; hemispherical "
                "measurements and emittance cannot be compared to planar TMM."
            )
        if self.polarization not in {"s", "p", "unpolarized"}:
            raise ValueError("Measurement polarization must be s, p or unpolarized")
        return self


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene: OpticalScene
    source_kind: Literal["touloukian", "ekhi", "csv"]
    source_reference: str = Field(min_length=5)
    source_locator: str = Field(min_length=1)
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    observations: list[Observation] = Field(default_factory=list, max_length=500)
    unavailable_reason: str | None = Field(default=None, min_length=10)

    @model_validator(mode="after")
    def require_observation_or_reason(self):
        if not self.observations and not self.unavailable_reason:
            raise ValueError("No comparable observations are available; provide unavailable_reason")
        if any(obs.source_kind != self.source_kind for obs in self.observations):
            raise ValueError("Observation source_kind must match request source_kind")
        if self.source_kind == "csv" and self.observations and not self.source_sha256:
            raise ValueError("CSV observations require source_sha256 for traceability")
        if self.source_kind == "csv" and any(obs.source_row is None for obs in self.observations):
            raise ValueError("CSV observations require source_row for traceability")
        return self


class CsvComparisonRequest(BaseModel):
    """A reproducible CSV upload envelope; the CSV itself contains observations."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    scene: OpticalScene
    source_reference: str = Field(min_length=5)
    source_locator: str = Field(min_length=1)
    csv_content: str = Field(min_length=1, max_length=5_000_000)


CSV_REQUIRED_COLUMNS = (
    "wavelength_nm",
    "measured_r",
    "measurement_type",
    "angle_deg",
    "polarization",
    "observed_conditions",
    "sample_description",
    "surface_finish",
    "surface_finish_class",
    "substrate_description",
    "substrate_model",
    "detector_geometry",
    "detector_geometry_class",
    "sample_model",
    "temperature_k",
    "atmosphere",
    "preparation",
)
CSV_OPTIONAL_COLUMNS = (
    "uncertainty_absolute",
    "uncertainty_method",
    "substrate_dataset_id",
)


def _normalise_text(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.split()).casefold()


def _blank_as_none(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()


def observations_from_csv(payload: CsvComparisonRequest) -> tuple[list[Observation], dict]:
    """Parse the documented S4 CSV schema without adding or inferring measurements."""

    reader = csv.DictReader(io.StringIO(payload.csv_content))
    if not reader.fieldnames:
        raise ValueError("CSV must include a header row")

    original_fieldnames = list(reader.fieldnames)
    fieldnames = [name.strip().lstrip("\ufeff") for name in original_fieldnames]
    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError("CSV contains duplicate column names")
    missing = sorted(set(CSV_REQUIRED_COLUMNS) - set(fieldnames))
    if missing:
        raise ValueError("missing required CSV columns: " + ", ".join(missing))

    observations: list[Observation] = []
    for row_number, raw_row in enumerate(reader, start=2):
        row = {
            fieldnames[index]: raw_row.get(original_fieldnames[index])
            for index in range(len(fieldnames))
        }
        if not any((value or "").strip() for value in row.values()):
            continue
        if None in raw_row:
            raise ValueError(f"CSV row {row_number} has more values than the header")

        observation_data = {
            "wavelength_nm": row.get("wavelength_nm"),
            "measured_r": row.get("measured_r"),
            "measurement_type": row.get("measurement_type"),
            "source_kind": "csv",
            "angle_deg": row.get("angle_deg"),
            "polarization": row.get("polarization"),
            "source_reference": payload.source_reference,
            "source_locator": f"{payload.source_locator}#row={row_number}",
            "observed_conditions": row.get("observed_conditions"),
            "geometry": {
                "sample_description": row.get("sample_description"),
                "surface_finish": row.get("surface_finish"),
                "surface_finish_class": _blank_as_none(row.get("surface_finish_class")),
                "substrate_description": _blank_as_none(row.get("substrate_description")),
                "substrate_model": _blank_as_none(row.get("substrate_model")),
                "substrate_dataset_id": _blank_as_none(row.get("substrate_dataset_id")),
                "detector_geometry": row.get("detector_geometry"),
                "detector_geometry_class": _blank_as_none(row.get("detector_geometry_class")),
                "sample_model": _blank_as_none(row.get("sample_model")),
            },
            "conditions": {
                "temperature_k": _blank_as_none(row.get("temperature_k")),
                "atmosphere": row.get("atmosphere"),
                "preparation": row.get("preparation"),
                "uncertainty_method": _blank_as_none(row.get("uncertainty_method")),
            },
            "uncertainty_absolute": _blank_as_none(row.get("uncertainty_absolute")),
            "source_row": row_number,
        }
        try:
            observations.append(Observation.model_validate(observation_data))
        except ValueError as exc:
            raise ValueError(f"CSV row {row_number} is invalid: {exc}") from exc

    return observations, {
        "format": "csv",
        "sha256": hashlib.sha256(payload.csv_content.encode("utf-8")).hexdigest(),
        "row_count": len(observations),
        "columns": fieldnames,
    }


def _ensure_compatible_observations(scene: OpticalScene, observations: list[Observation]) -> None:
    first = observations[0]
    geometry_fields = (
        "sample_description",
        "surface_finish",
        "substrate_description",
        "surface_finish_class",
        "substrate_model",
        "substrate_dataset_id",
        "detector_geometry",
        "detector_geometry_class",
        "sample_model",
    )
    condition_fields = ("temperature_k", "atmosphere", "preparation", "uncertainty_method")

    first_geometry = {
        field: _normalise_text(getattr(first.geometry, field)) for field in geometry_fields
    }
    first_conditions = {
        field: (
            getattr(first.conditions, field)
            if field == "temperature_k"
            else _normalise_text(getattr(first.conditions, field))
        )
        for field in condition_fields
    }
    detector = first_geometry["detector_geometry"] or ""
    if "specular" not in detector or not (
        "directional" in detector or "angle-resolved" in detector
    ):
        raise ValueError(
            "Observation detector geometry is incompatible: planar TMM comparison "
            "requires a specular directional or angle-resolved detector"
        )
    surface_finish = first_geometry["surface_finish"] or ""
    surface_class = first_geometry["surface_finish_class"]
    if (
        surface_class in {"rough", "unknown"}
        or "rough" in surface_finish
        or "diffus" in surface_finish
    ):
        raise ValueError(
            "Observation surface geometry is incompatible: rough or diffuse surfaces "
            "require a different forward model than planar specular TMM"
        )
    if first.geometry.sample_model != "planar_stack":
        raise ValueError("Observation sample geometry is incompatible with planar stack TMM")
    if first.geometry.substrate_model != "semi_infinite_exit_medium":
        raise ValueError(
            "Observation substrate geometry is incompatible: expected the semi-infinite "
            "exit medium used by planar TMM"
        )
    if first.geometry.detector_geometry_class not in {"specular_directional", "angle_resolved"}:
        raise ValueError(
            "Observation detector geometry is incompatible: expected specular_directional "
            "or angle_resolved"
        )
    if _normalise_text(first.conditions.atmosphere) != _normalise_text(
        scene.environment.incident_medium
    ):
        raise ValueError("Observation atmosphere does not match the scene incident medium")
    if (
        first.geometry.substrate_dataset_id is not None
        and first.geometry.substrate_dataset_id != scene.environment.exit_medium_dataset_id
    ):
        raise ValueError("Observation substrate dataset does not match the scene exit medium")

    for index, observation in enumerate(observations[1:], start=2):
        geometry = {
            field: _normalise_text(getattr(observation.geometry, field))
            for field in geometry_fields
        }
        if geometry != first_geometry:
            differing = next(
                field for field in geometry_fields if geometry[field] != first_geometry[field]
            )
            raise ValueError(f"Observation geometry is inconsistent for {differing} at row {index}")
        conditions = {
            field: (
                getattr(observation.conditions, field)
                if field == "temperature_k"
                else _normalise_text(getattr(observation.conditions, field))
            )
            for field in condition_fields
        }
        if conditions != first_conditions:
            differing = next(
                field for field in condition_fields if conditions[field] != first_conditions[field]
            )
            raise ValueError(
                f"Observation conditions are inconsistent for {differing} at row {index}"
            )
        if observation.polarization != first.polarization:
            raise ValueError(f"Observation polarization is inconsistent at row {index}")
        if abs(observation.angle_deg - first.angle_deg) > 1e-6:
            raise ValueError(f"Observation angle is inconsistent at row {index}")


def compare_observations(database: str, request: ComparisonRequest) -> dict:
    if not request.observations:
        return {
            "status": "unavailable",
            "count": 0,
            "metrics": None,
            "points": [],
            "source": _source_metadata(request),
            "reason": request.unavailable_reason,
            "verification_status": "no_comparable_observations_available",
            "warning": (
                "No legally available, traceable and physically comparable observations "
                "were supplied; no validation claim is made."
            ),
        }
    scene = request.scene
    if scene.environment.incident_medium.lower() != "air":
        raise ValueError("Only air incidence is supported by the comparison")
    _ensure_compatible_observations(scene, request.observations)
    series = []
    for obs in request.observations:
        if abs(obs.angle_deg - scene.incidence.angle_deg) > 1e-6:
            raise ValueError("Observation angle does not match scene angle")
        if obs.polarization != scene.incidence.polarization:
            raise ValueError("Observation polarization does not match scene polarization")
        predicted = simulate_planar(database, scene, obs.wavelength_nm, obs.polarization)
        residual = predicted.reflectance - obs.measured_r
        if not isfinite(residual):
            raise ValueError("Non-finite prediction residual")
        series.append(
            {
                "wavelength_nm": obs.wavelength_nm,
                "measured_R": obs.measured_r,
                "predicted_R": predicted.reflectance,
                "residual_model_minus_observed": residual,
                "absolute_error": abs(residual),
                "uncertainty_absolute": obs.uncertainty_absolute,
                "source_row": obs.source_row,
                "source_sha256": request.source_sha256,
                "source_reference": obs.source_reference,
                "source_locator": obs.source_locator,
                "observed_conditions": obs.observed_conditions,
                "source_kind": obs.source_kind,
                "geometry": obs.geometry.model_dump(),
                "conditions": obs.conditions.model_dump(),
            }
        )
    n = len(series)
    mae = sum(x["absolute_error"] for x in series) / n
    rmse = sqrt(sum(x["residual_model_minus_observed"] ** 2 for x in series) / n)
    return {
        "status": "comparison_computed",
        "count": n,
        "metrics": {"MAE": mae, "RMSE": rmse, "units": "absolute reflectance fraction"},
        "points": series,
        "source": _source_metadata(request),
        "model": "planar ideal-interface TMM; specular directional reflectance",
        "verification_status": "user_supplied_observations_not_independently_verified",
        "warning": (
            "This is a numerical comparison, NOT a scientific validation "
            "of Touloukian/EKHI. Verify samples, roughness, temperature, "
            "angle, polarization, surface finish, spectrum and bibliographic "
            "provenance independently before drawing conclusions."
        ),
    }


def _source_metadata(request: ComparisonRequest) -> dict:
    source = {
        "kind": request.source_kind,
        "reference": request.source_reference,
        "locator": request.source_locator,
    }
    if request.source_sha256:
        source["sha256"] = request.source_sha256
    return source


def compare_csv_observations(database: str, payload: CsvComparisonRequest) -> dict:
    observations, csv_source = observations_from_csv(payload)
    request = ComparisonRequest.model_validate(
        {
            "scene": payload.scene,
            "source_kind": "csv",
            "source_reference": payload.source_reference,
            "source_locator": payload.source_locator,
            "source_sha256": hashlib.sha256(payload.csv_content.encode("utf-8")).hexdigest(),
            "observations": [observation.model_dump() for observation in observations],
            "unavailable_reason": (
                "CSV contains no non-blank observation rows; no comparable measurement is available."
                if not observations
                else None
            ),
        }
    )
    result = compare_observations(database, request)
    result["source"].update(csv_source)
    return result
