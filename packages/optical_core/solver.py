"""Physical Fresnel and transfer-matrix calculations for plane parallel films.

The solver uses the independently published 'tmm' reference implementation
(S. J. Byrnes, arXiv:1603.02720), and *only* optical constants sourced from
one explicitly chosen dataset per medium. No Three.js or fabricated indices.

Conventions: n_complex = n + i k, k >= 0, vacuum wavelengths and physical
layer thicknesses both in nm. Incident medium is transparent air (n=1).
The last medium is semi-infinite: T is energy crossing INTO it and not the
through-sample transmission of an infinite piece of metal.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf, isclose, isfinite, pi, radians

import numpy as np
import tmm

from apps.api.models import OpticalScene
from packages.material_data.store import evaluate_constants


@dataclass(frozen=True)
class OpticalPower:
    wavelength_nm: float
    polarization: str
    reflectance: float
    transmittance: float
    absorptance: float
    finite_layer_absorption: tuple[float, ...]
    exit_medium_absorption: float | None
    interpretation: str


def absorption_coefficient(k: float, wavelength_nm: float) -> float:
    """Bulk alpha [m^-1], for dimensionless extinction coefficient k."""
    if not (isfinite(k) and k >= 0 and isfinite(wavelength_nm) and wavelength_nm > 0):
        raise ValueError("k and wavelength must be finite; k>=0 and lambda>0")
    return 4 * pi * k / (wavelength_nm * 1e-9)


def interface_reflectance(n: float, k: float = 0.0) -> float:
    """Fresnel normal-incidence R for air -> passive material."""
    if not (isfinite(n) and n > 0 and isfinite(k) and k >= 0):
        raise ValueError("n>0 and k>=0 required")
    return ((n - 1) ** 2 + k**2) / ((n + 1) ** 2 + k**2)


def _constant_from_dataset(database: str, dataset_id: str, wavelength_nm: float) -> complex:
    record = evaluate_constants(database, dataset_id, wavelength_nm, require_nk=True)
    if record["k"] is None:
        raise ValueError("Missing extinction coefficient k")
    return complex(record["n"], record["k"])


def simulate_planar(
    database: str,
    scene: OpticalScene,
    wavelength_nm: float,
    polarization: str,
) -> OpticalPower:
    """Calculate a physically supported laser/stack point.

    Coherent and mixed incoherent stacks are supported. An unpolarized result
    is the arithmetic mean of independent s and p intensity calculations.
    """
    if not isfinite(wavelength_nm) or wavelength_nm <= 0:
        raise ValueError("wavelength_nm must be positive and finite")
    if polarization == "unpolarized":
        s = simulate_planar(database, scene, wavelength_nm, "s")
        p = simulate_planar(database, scene, wavelength_nm, "p")
        return OpticalPower(
            wavelength_nm, "unpolarized",
            (s.reflectance + p.reflectance) / 2,
            (s.transmittance + p.transmittance) / 2,
            (s.absorptance + p.absorptance) / 2,
            tuple((a + b) / 2 for a, b in zip(
                s.finite_layer_absorption, p.finite_layer_absorption, strict=True
            )),
            (
                None if s.exit_medium_absorption is None or p.exit_medium_absorption is None
                else (s.exit_medium_absorption + p.exit_medium_absorption) / 2
            ),
            s.interpretation,
        )
    if polarization not in {"s", "p"}:
        raise ValueError(f"Unsupported polarization: {polarization}")
    if scene.environment.incident_medium.lower() != "air":
        raise ValueError("S2 only supports transparent air as incident medium")
    n_list = [complex(1.0, 0.0)]
    for layer in scene.layers:
        n_list.append(_constant_from_dataset(database, layer.dataset_id, wavelength_nm))
    n_list.append(
        _constant_from_dataset(database, scene.environment.exit_medium_dataset_id, wavelength_nm)
    )
    thicknesses = [inf] + [layer.thickness_nm for layer in scene.layers] + [inf]
    theta_rad = radians(scene.incidence.angle_deg)
    if all(layer.coherence == "coherent" for layer in scene.layers):
        outcome = tmm.coh_tmm(polarization, n_list, thicknesses, theta_rad, wavelength_nm)
        absorption = tmm.absorp_in_each_layer(outcome)
    else:
        coherence = ["i"] + [
            "c" if layer.coherence == "coherent" else "i" for layer in scene.layers
        ] + ["i"]
        outcome = tmm.inc_tmm(
            polarization, n_list, thicknesses, coherence, theta_rad, wavelength_nm
        )
        absorption = tmm.inc_absorp_in_each_layer(outcome)
    r, transmitted = float(outcome["R"]), float(outcome["T"])
    absorbed = 1.0 - r - transmitted
    if not all(isfinite(z) for z in (r, transmitted, absorbed)):
        raise ValueError("Non-finite TMM outcome")
    if not isclose(r + transmitted + absorbed, 1.0, abs_tol=1e-9):
        raise ValueError("Energy balance failure")
    if r < -1e-8 or transmitted < -1e-8 or absorbed < -1e-8:
        raise ValueError("Unphysical passive-medium energy fractions")
    finite = tuple(float(x) for x in absorption[1:-1])
    if len(finite) != len(scene.layers):
        raise ValueError("Absorption indexing did not match layer count")
    if abs(sum(finite) - absorbed) > 1e-6:
        raise ValueError("Finite-layer absorption inconsistent with R/T/A")
    return OpticalPower(
        wavelength_nm=wavelength_nm,
        polarization=polarization,
        reflectance=r,
        transmittance=transmitted,
        absorptance=absorbed,
        finite_layer_absorption=finite,
        exit_medium_absorption=transmitted if n_list[-1].imag > 0 else None,
        interpretation=(
            "T is the energy flux entering the semi-infinite exit medium; "
            "it is not the light exiting the far side of an infinite substrate. "
            "A is absorption within the finite coating layers only. If the exit "
            "medium is absorbing, transmitted flux is eventually dissipated there."
        ),
    )


def simulate_laser(database: str, scene: OpticalScene) -> OpticalPower:
    """Run one point for a monochromatic laser; solar/lamp are a later sprint."""
    if scene.source.type != "laser":
        raise ValueError("S2 supports laser sources only; spectra arrive in S3")
    return simulate_planar(
        database, scene, scene.source.wavelength_nm, scene.incidence.polarization
    )


def scan_spectrum(
    database: str,
    scene: OpticalScene,
    wavelengths_nm: list[float],
) -> list[OpticalPower]:
    """Evaluate a user-provided in-domain spectral grid, rejecting invalid data."""
    if not wavelengths_nm or len(wavelengths_nm) > 2000:
        raise ValueError("Spectral grid must contain 1..2000 wavelengths")
    if any(not isfinite(w) or w <= 0 for w in wavelengths_nm):
        raise ValueError("All wavelengths must be finite and positive")
    return [
        simulate_planar(database, scene, w, scene.incidence.polarization)
        for w in wavelengths_nm
    ]
