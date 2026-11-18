"""Compare physical TMM predictions with user-supplied, traceable measurements.

No Touloukian or EKHI measurements are bundled or fabricated. An observation
must describe specular reflectance at an angle and polarization compatible with
the model. Hemispherical reflectance and thermal emittance are not comparable
to the planar specular calculation without a different forward model.
"""

from __future__ import annotations

from math import isfinite, sqrt

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.api.models import OpticalScene
from packages.optical_core.solver import simulate_planar


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    wavelength_nm: float = Field(gt=0)
    measured_r: float = Field(ge=0, le=1)
    measurement_type: str = Field(default="specular_reflectance")
    angle_deg: float = Field(ge=0, lt=90)
    polarization: str
    source_reference: str = Field(min_length=5)
    source_locator: str = Field(min_length=1)
    observed_conditions: str = Field(min_length=5)
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
    observations: list[Observation] = Field(min_length=1, max_length=500)


def compare_observations(database: str, request: ComparisonRequest) -> dict:
    scene = request.scene
    if scene.environment.incident_medium.lower() != "air":
        raise ValueError("Only air incidence is supported by the comparison")
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
        series.append({
            "wavelength_nm": obs.wavelength_nm,
            "measured_R": obs.measured_r,
            "predicted_R": predicted.reflectance,
            "residual_model_minus_observed": residual,
            "absolute_error": abs(residual),
            "uncertainty_absolute": obs.uncertainty_absolute,
            "source_reference": obs.source_reference,
            "source_locator": obs.source_locator,
            "observed_conditions": obs.observed_conditions,
        })
    n = len(series)
    mae = sum(x["absolute_error"] for x in series) / n
    rmse = sqrt(sum(x["residual_model_minus_observed"] ** 2 for x in series) / n)
    return {
        "status": "comparison_computed",
        "count": n,
        "metrics": {"MAE": mae, "RMSE": rmse, "units": "absolute reflectance fraction"},
        "points": series,
        "model": "planar ideal-interface TMM; specular directional reflectance",
        "verification_status": "user_supplied_observations_not_independently_verified",
        "warning": (
            "This is a numerical comparison, NOT a scientific validation "
            "of Touloukian/EKHI. Verify samples, roughness, temperature, "
            "angle, polarization, surface finish, spectrum and bibliographic "
            "provenance independently before drawing conclusions."
        ),
    }
