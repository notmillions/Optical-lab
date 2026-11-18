"""Versioned validation contracts for planar optical scenes.

S0 does NOT provide a material database or a physical solver. These models
validate configuration only and must not be interpreted as simulation results.
"""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class LaserSource(StrictModel):
    type: Literal["laser"] = "laser"
    wavelength_nm: float = Field(gt=0)
    power_w: float | None = Field(default=None, ge=0)


class SolarSource(StrictModel):
    type: Literal["solar"] = "solar"
    spectrum_id: str = Field(min_length=1)


class LampSource(StrictModel):
    type: Literal["lamp"] = "lamp"
    spectrum_id: str = Field(min_length=1)


LightSource = Annotated[
    LaserSource | SolarSource | LampSource, Field(discriminator="type")
]


class Incidence(StrictModel):
    angle_deg: float = Field(default=0, ge=0, lt=90)
    polarization: Literal["s", "p", "unpolarized"] = "unpolarized"


class Environment(StrictModel):
    incident_medium: str = Field(default="air", min_length=1)
    exit_medium_dataset_id: str = Field(min_length=1)


class OpticalLayer(StrictModel):
    id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    thickness_nm: float = Field(gt=0)
    coherence: Literal["coherent", "incoherent"] = "coherent"


class OpticalScene(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    kind: Literal["planar-stack"] = "planar-stack"
    source: LightSource
    incidence: Incidence
    environment: Environment
    layers: list[OpticalLayer] = Field(min_length=1, max_length=200)
    solver: Literal["planar-tmm"] = "planar-tmm"

    @model_validator(mode="after")
    def unique_layer_ids(self) -> Self:
        ids = [layer.id for layer in self.layers]
        if len(ids) != len(set(ids)):
            raise ValueError("Layer IDs must be unique")
        return self


class OpticalDataset(StrictModel):
    """Dataset metadata; no guessed refractive-index values are stored here."""

    id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    source_snapshot: str = Field(min_length=1)
    wavelength_min_nm: float = Field(gt=0)
    wavelength_max_nm: float = Field(gt=0)
    has_n: bool
    has_k: bool
    references: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_domain(self) -> Self:
        if self.wavelength_min_nm >= self.wavelength_max_nm:
            raise ValueError("Invalid wavelength domain")
        return self


class OpticalConstants(StrictModel):
    wavelength_nm: float = Field(gt=0)
    n: float = Field(gt=0)
    k: float | None = Field(default=None, ge=0)


class SpectralPoint(StrictModel):
    wavelength_nm: float = Field(gt=0)
    reflectance: float = Field(ge=0, le=1)
    transmittance: float = Field(ge=0, le=1)
    absorptance: float = Field(ge=0, le=1)


class SimulationResult(StrictModel):
    """Future solver output contract, not instantiated by the S0 application."""

    scene_schema_version: Literal["1.0"]
    solver_version: str = Field(min_length=1)
    source_snapshot: str = Field(min_length=1)
    points: list[SpectralPoint] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)


class SceneValidation(StrictModel):
    valid: bool
    schema_version: Literal["1.0"]
    layer_count: int = Field(ge=1)
    warning: str
