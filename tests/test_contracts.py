"""Contract tests; values are metadata-only and never simulated."""

import pytest
from pydantic import ValidationError

from apps.api.models import OpticalConstants, OpticalDataset


def test_rejects_reversed_spectral_domain() -> None:
    with pytest.raises(ValidationError, match="Invalid wavelength domain"):
        OpticalDataset(
            id="example",
            material_id="SiO2",
            source_snapshot="test-snapshot",
            wavelength_min_nm=900,
            wavelength_max_nm=200,
            has_n=True,
            has_k=False,
        )


def test_missing_k_is_explicit_not_zero() -> None:
    constants = OpticalConstants(wavelength_nm=532, n=1.5)
    assert constants.k is None


def test_rejects_nonfinite_values() -> None:
    with pytest.raises(ValidationError):
        OpticalConstants(wavelength_nm=532, n=float("nan"), k=0)
