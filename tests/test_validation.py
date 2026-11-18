"""Numerical reference-comparison tests use synthetic observations only."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.models import OpticalScene
from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets
from packages.optical_core.solver import simulate_planar
from packages.validation.comparison import ComparisonRequest, compare_observations

SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"


@pytest.fixture
def reference_setup(tmp_path, monkeypatch):
    db = tmp_path / "comparison.sqlite"
    records = []
    for material, n, k in (("GlassTest", 1.5, 0), ("AirTest", 1, 0)):
        content = (
            f'REFERENCES: "Synthetic optical fixture, not measurements"\n'
            "DATA:\n"
            "  - type: tabulated nk\n"
            "    data: |\n"
            f"      0.450 {n} {k}\n"
            f"      0.532 {n} {k}\n"
            f"      0.650 {n} {k}\n"
        ).encode()
        records.append(
            parse_dataset(f"database/data/main/{material}/nk/Test.yml", content, SNAPSHOT)
        )
    import_datasets(db, records)
    monkeypatch.setenv("OPTICAL_LAB_DB", str(db))
    scene = OpticalScene.model_validate({
        "kind": "planar-stack",
        "source": {"type": "laser", "wavelength_nm": 532},
        "incidence": {"angle_deg": 30, "polarization": "s"},
        "environment": {
            "incident_medium": "air",
            "exit_medium_dataset_id": "main:AirTest:nk:Test",
        },
        "layers": [{
            "id": "glass",
            "dataset_id": "main:GlassTest:nk:Test",
            "thickness_nm": 100,
        }],
    })
    return str(db), scene


def _observation(measured: float, angle: float = 30, type_: str = "specular_reflectance"):
    return {
        "wavelength_nm": 532,
        "measured_r": measured,
        "measurement_type": type_,
        "angle_deg": angle,
        "polarization": "s",
        "source_reference": "Synthetic test-only reference (not Touloukian)",
        "source_locator": "test fixture, generated in test_validation.py",
        "observed_conditions": "Synthetic ideal interface; no measured sample",
    }


def test_comparison_equal_model_and_synthetic_observation(reference_setup):
    db, scene = reference_setup
    model_value = simulate_planar(db, scene, 532, "s").reflectance
    request = ComparisonRequest.model_validate({
        "scene": scene.model_dump(),
        "observations": [_observation(model_value), _observation(model_value + 0.01)],
    })
    response = compare_observations(db, request)
    assert response["metrics"]["MAE"] == pytest.approx(0.005)
    assert response["metrics"]["RMSE"] == pytest.approx((0.0001 / 2) ** 0.5)
    assert response["verification_status"] == "user_supplied_observations_not_independently_verified"
    assert "NOT a scientific validation" in response["warning"]


def test_api_comparison_returns_provenance(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post("/api/v1/validation/compare", json={
        "scene": scene.model_dump(),
        "observations": [_observation(0.1)],
    })
    assert response.status_code == 200, response.text
    assert response.json()["points"][0]["source_reference"].startswith("Synthetic")


def test_mismatched_incidence_rejected(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post("/api/v1/validation/compare", json={
        "scene": scene.model_dump(),
        "observations": [_observation(0.1, angle=45)],
    })
    assert response.status_code == 422
    assert "angle" in response.json()["detail"]


def test_hemispherical_values_not_falsely_compared(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post("/api/v1/validation/compare", json={
        "scene": scene.model_dump(),
        "observations": [_observation(0.1, type_="hemispherical_reflectance")],
    })
    assert response.status_code == 422


def test_emittance_not_supported(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post("/api/v1/validation/compare", json={
        "scene": scene.model_dump(),
        "observations": [_observation(0.1, type_="emittance")],
    })
    assert response.status_code == 422
