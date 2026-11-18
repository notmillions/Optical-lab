"""Documented solar and incandescent reference spectra for Optical Lab.

Solar data: ASTM G173-03 reference spectrum bundled by pvlib (source NREL).
Lamp: *ideal Planck radiator at 2856 K*, a theoretical incandescent model.
The latter is NOT marketed as a measured LED spectrum or as a digital copy
of the normative CIE A table.

Spectrum weights represent density *per nm*, not discrete photon counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np


@dataclass(frozen=True)
class SourceSpectrum:
    id: str
    kind: str
    wavelengths_nm: tuple[float, ...]
    weights: tuple[float, ...]
    units: str
    reference: str
    assumption: str


def solar_reference(spectrum_id: str) -> SourceSpectrum:
    """Get the real ASTM G173 reference dataset from pvlib's local package."""
    if spectrum_id not in {"ASTM-G173-global", "ASTM-G173-direct"}:
        raise ValueError(
            "Unsupported solar spectrum ID. Use ASTM-G173-global or ASTM-G173-direct"
        )
    from pvlib import spectrum

    data = spectrum.get_reference_spectra(standard="ASTM G173-03")
    column = "global" if spectrum_id.endswith("global") else "direct"
    wavelengths = tuple(float(value) for value in data.index)
    weights = tuple(float(value) for value in data[column].to_numpy())
    if len(wavelengths) < 2 or any(w < 0 or not isfinite(w) for w in weights):
        raise ValueError("Invalid built-in ASTM G173 spectrum")
    return SourceSpectrum(
        spectrum_id,
        "solar",
        wavelengths,
        weights,
        "W m^-2 nm^-1",
        "ASTM G173-03 reference spectra, NREL dataset included with pvlib-python",
        (
            "Fixed ASTM AM1.5 reference spectral irradiance. "
            "The TMM solver treats each wavelength as one plane wave at the "
            "configured incidence angle; diffuse angular distributions are "
            "NOT simulated, including for the global spectrum."
        ),
    )


def incandescent_reference(spectrum_id: str) -> SourceSpectrum:
    """Idealized thermal source at 2856K, relative spectral radiance per nm."""
    if spectrum_id != "incandescent-2856K-planck":
        raise ValueError("Unsupported lamp spectrum ID")
    # CODATA exact SI constants h, c, k (constants exact in current SI).
    h = 6.62607015e-34
    c = 299792458.0
    boltzmann = 1.380649e-23
    wavelengths = np.arange(380.0, 781.0, 5.0)
    lambdas_m = wavelengths * 1e-9
    exponent = h * c / (lambdas_m * boltzmann * 2856.0)
    radiance = (2 * h * c * c / (lambdas_m**5)) / np.expm1(exponent)
    relative = radiance / np.max(radiance)
    return SourceSpectrum(
        spectrum_id,
        "lamp",
        tuple(float(x) for x in wavelengths),
        tuple(float(x) for x in relative),
        "relative spectral radiance nm^-1",
        "Planck law with exact SI constants, temperature 2856 K; ideal incandescent model",
        (
            "Only visible range 380..780 nm is represented. Not a measured "
            "lamp and not a normative CIE illuminant table. Distribution in "
            "angle or absolute watts is not modelled."
        ),
    )


def get_spectrum(source_type: str, spectrum_id: str) -> SourceSpectrum:
    if source_type == "solar":
        return solar_reference(spectrum_id)
    if source_type == "lamp":
        return incandescent_reference(spectrum_id)
    raise ValueError("Spectral source type must be solar or lamp")


def reference_sources() -> list[dict[str, str]]:
    return [
        {
            "type": "laser",
            "id": "monochromatic",
            "label": "Laser monochromatique idéal (nm configurables)",
        },
        {"type": "solar", "id": "ASTM-G173-global", "label": "Soleil ASTM G173 global"},
        {"type": "solar", "id": "ASTM-G173-direct", "label": "Soleil ASTM G173 direct"},
        {
            "type": "lamp",
            "id": "incandescent-2856K-planck",
            "label": "Incandescente théorique — Planck 2856 K",
        },
    ]
