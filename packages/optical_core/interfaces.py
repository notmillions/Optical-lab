"""Ports for the optical solver and data providers.

Adapters can be built in later sprints without coupling physics to Three.js.
"""

from typing import Protocol

from apps.api.models import (
    OpticalConstants,
    OpticalDataset,
    OpticalScene,
    SimulationResult,
)


class MaterialProvider(Protocol):
    def get_dataset(self, dataset_id: str) -> OpticalDataset:
        """Return a specific source-backed dataset, or raise if unavailable."""
        ...

    def evaluate(self, dataset_id: str, wavelength_nm: float) -> OpticalConstants:
        """Resolve n and k in-domain, never extrapolate or impute silently."""
        ...


class LightSourceProvider(Protocol):
    def spectrum(self, source_id: str) -> list[tuple[float, float]]:
        """Return wavelength_nm and documented spectral weight pairs."""
        ...


class SimulationEngine(Protocol):
    def validate(self, scene: OpticalScene) -> None:
        """Reject unsupported geometries, domains, or missing properties."""
        ...

    def run(self, scene: OpticalScene) -> SimulationResult:
        """Compute a reproducible physical result with provenance."""
        ...
