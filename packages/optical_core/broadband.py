"""Energy-weighted response to broadband solar and lamp spectra.

Never present these as angle-resolved radiative-transfer simulations: each
wavelength is treated as a plane wave at ONE chosen incidence angle. Coverage
reports which fraction of reference-source energy lies in the compatible
optical-data window. Only that window is normalized for effective R/T/A.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from apps.api.models import OpticalScene
from packages.material_data.store import dataset_details
from packages.optical_core.solver import OpticalPower, simulate_planar
from packages.optical_core.spectra import SourceSpectrum, get_spectrum


@dataclass(frozen=True)
class SpectralAggregate:
    source: SourceSpectrum
    points: tuple[OpticalPower, ...]
    effective_r: float
    effective_t: float
    effective_a: float
    reference_coverage: float
    covered_nm: tuple[float, float]
    incident_power_note: str


def _material_window(database: str, scene: OpticalScene) -> tuple[float, float]:
    ids = [layer.dataset_id for layer in scene.layers] + [
        scene.environment.exit_medium_dataset_id
    ]
    details = [dataset_details(database, dataset_id) for dataset_id in ids]
    missing = [record["id"] for record in details if not record["has_n"] or not record["has_k"]]
    if missing:
        raise ValueError(
            "Spectral integration requires both n and k in every selected source: "
            + ", ".join(missing)
        )
    return max(record["min_nm"] for record in details), min(
        record["max_nm"] for record in details
    )


def aggregate_source(
    database: str,
    scene: OpticalScene,
    *,
    max_wavelengths: int = 160,
) -> SpectralAggregate:
    """Compute broadband R/T/A on the common supported spectral region."""
    if scene.source.type not in {"solar", "lamp"}:
        raise ValueError("Broadband source must be solar or lamp")
    if not 2 <= max_wavelengths <= 1000:
        raise ValueError("max_wavelengths must lie between 2 and 1000")
    spectrum = get_spectrum(scene.source.type, scene.source.spectrum_id)
    wavelengths = np.asarray(spectrum.wavelengths_nm, dtype=float)
    densities = np.asarray(spectrum.weights, dtype=float)
    if (
        len(wavelengths) < 2
        or not np.all(np.isfinite(wavelengths))
        or not np.all(np.isfinite(densities))
        or np.any(densities < 0)
        or not np.all(np.diff(wavelengths) > 0)
    ):
        raise ValueError("Invalid source spectrum")
    # NumPy 1.26 is still supported by pyproject.toml; trapezoid was added in 2.0.
    integrate = getattr(np, "trapezoid", np.trapz)
    full_energy = float(integrate(densities, wavelengths))
    if not isfinite(full_energy) or full_energy <= 0:
        raise ValueError("Source has zero or invalid integrated spectral weight")
    minimum, maximum = _material_window(database, scene)
    selector = (wavelengths >= minimum) & (wavelengths <= maximum)
    valid = np.nonzero(selector)[0]
    if len(valid) < 2:
        raise ValueError("No usable shared spectral interval for the source and materials")

    # Downsample for bounded, interactive compute cost, using the source grid.
    if len(valid) > max_wavelengths:
        selected = np.linspace(0, len(valid) - 1, max_wavelengths)
        valid = valid[np.unique(np.rint(selected).astype(int))]
    sampled_nm = wavelengths[valid]
    sampled_weights = densities[valid]
    denominator = float(integrate(sampled_weights, sampled_nm))
    if denominator <= 0:
        raise ValueError("No positive spectral weight in the common data domain")
    # Full source coverage calculation is performed on original native grid.
    native_nm = wavelengths[selector]
    native_densities = densities[selector]
    native_coverage = float(np.trapezoid(native_densities, native_nm) / full_energy)

    points = tuple(
        simulate_planar(database, scene, float(w), scene.incidence.polarization)
        for w in sampled_nm
    )
    r = float(
        integrate(np.asarray([p.reflectance for p in points]) * sampled_weights,
                  sampled_nm) / denominator
    )
    t = float(
        integrate(np.asarray([p.transmittance for p in points]) * sampled_weights,
                  sampled_nm) / denominator
    )
    a = float(
        integrate(np.asarray([p.absorptance for p in points]) * sampled_weights,
                  sampled_nm) / denominator
    )
    if abs(r + t + a - 1.0) > 1e-6:
        raise ValueError("Integrated energy conservation failed")
    return SpectralAggregate(
        source=spectrum,
        points=points,
        effective_r=r,
        effective_t=t,
        effective_a=a,
        reference_coverage=native_coverage,
        covered_nm=(float(native_nm[0]), float(native_nm[-1])),
        incident_power_note=(
            "R/T/A represent source-energy-weighted fractions on the shared "
            "spectral domain, not absolute output in watts. When the reference "
            "coverage is below 100%, these averages cannot be extrapolated to "
            "the unmeasured spectrum. Source angular distribution is not modelled."
        ),
    )
