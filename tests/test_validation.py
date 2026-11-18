"""Numerical reference-comparison tests use synthetic observations only."""

from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.models import OpticalScene
from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets
from packages.optical_core.solver import simulate_planar
from packages.validation.comparison import ComparisonRequest, compare_observations

SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"
CSV_SHA256 = "a" * 64


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
    scene = OpticalScene.model_validate(
        {
            "kind": "planar-stack",
            "source": {"type": "laser", "wavelength_nm": 532},
            "incidence": {"angle_deg": 30, "polarization": "s"},
            "environment": {
                "incident_medium": "air",
                "exit_medium_dataset_id": "main:AirTest:nk:Test",
            },
            "layers": [
                {
                    "id": "glass",
                    "dataset_id": "main:GlassTest:nk:Test",
                    "thickness_nm": 100,
                }
            ],
        }
    )
    return str(db), scene


def _observation(
    measured: float,
    angle: float = 30,
    type_: str = "specular_reflectance",
    *,
    atmosphere: str = "air",
    temperature_k: float | None = 293.15,
    surface_finish_class: str = "smooth",
    source_row: int = 2,
):
    return {
        "wavelength_nm": 532,
        "measured_r": measured,
        "measurement_type": type_,
        "source_kind": "csv",
        "angle_deg": angle,
        "polarization": "s",
        "source_reference": "Synthetic test-only reference (not Touloukian)",
        "source_locator": "test fixture, generated in test_validation.py",
        "source_row": source_row,
        "observed_conditions": "Synthetic ideal interface; no measured sample",
        "geometry": {
            "sample_description": "Synthetic planar test interface",
            "surface_finish": "ideal smooth surface",
            "surface_finish_class": surface_finish_class,
            "substrate_description": "semi-infinite air fixture",
            "substrate_model": "semi_infinite_exit_medium",
            "detector_geometry": "specular directional detector",
            "detector_geometry_class": "specular_directional",
            "sample_model": "planar_stack",
        },
        "conditions": {
            "temperature_k": temperature_k,
            "atmosphere": atmosphere,
            "preparation": "synthetic fixture; no physical sample",
            "uncertainty_method": "not applicable",
        },
    }


def test_comparison_equal_model_and_synthetic_observation(reference_setup):
    db, scene = reference_setup
    model_value = simulate_planar(db, scene, 532, "s").reflectance
    request = ComparisonRequest.model_validate(
        {
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(model_value), _observation(model_value + 0.01)],
        }
    )
    response = compare_observations(db, request)
    assert response["metrics"]["MAE"] == pytest.approx(0.005)
    assert response["metrics"]["RMSE"] == pytest.approx((0.0001 / 2) ** 0.5)
    assert (
        response["verification_status"] == "user_supplied_observations_not_independently_verified"
    )
    assert "NOT a scientific validation" in response["warning"]


def test_api_comparison_returns_provenance(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(0.1)],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["points"][0]["source_reference"].startswith("Synthetic")


def test_csv_comparison_preserves_file_hash_and_row_provenance(reference_setup):
    _, scene = reference_setup
    csv_content = (
        "wavelength_nm,measured_r,measurement_type,angle_deg,polarization,"
        "observed_conditions,sample_description,surface_finish,surface_finish_class,"
        "substrate_description,substrate_model,detector_geometry,detector_geometry_class,"
        "sample_model,temperature_k,atmosphere,preparation,uncertainty_absolute,"
        "uncertainty_method\n"
        "532,0.1,specular_reflectance,30,s,air at 293.15 K,"
        "synthetic planar interface,ideal smooth surface,smooth,semi-infinite air fixture,"
        "semi_infinite_exit_medium,specular directional detector,specular_directional,"
        "planar_stack,293.15,air,synthetic fixture,,not applicable\n"
    )
    response = TestClient(app).post(
        "/api/v1/validation/compare-csv",
        json={
            "scene": scene.model_dump(),
            "source_reference": "Synthetic CSV fixture for parser contract",
            "source_locator": "tests/test_validation.py::csv-fixture",
            "csv_content": csv_content,
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["source"]["format"] == "csv"
    assert result["source"]["row_count"] == 1
    assert result["source"]["sha256"] == sha256(csv_content.encode()).hexdigest()
    assert result["points"][0]["source_locator"].endswith("#row=2")
    assert result["verification_status"] == (
        "user_supplied_observations_not_independently_verified"
    )


def test_csv_comparison_rejects_missing_traceability_columns(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare-csv",
        json={
            "scene": scene.model_dump(),
            "source_reference": "Synthetic CSV fixture for parser contract",
            "source_locator": "tests/test_validation.py::missing-columns",
            "csv_content": "wavelength_nm,measured_r\n532,0.1\n",
        },
    )
    assert response.status_code == 422
    assert "missing required CSV columns" in response.json()["detail"]


def test_csv_empty_is_explicitly_unavailable(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare-csv",
        json={
            "scene": scene.model_dump(),
            "source_reference": "User CSV with no observations",
            "source_locator": "user-upload.csv",
            "csv_content": "wavelength_nm,measured_r,measurement_type,angle_deg,polarization,"
            "observed_conditions,sample_description,surface_finish,surface_finish_class,"
            "substrate_description,substrate_model,detector_geometry,detector_geometry_class,"
            "sample_model,temperature_k,atmosphere,preparation,uncertainty_absolute,"
            "uncertainty_method\n",
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "unavailable"
    assert result["verification_status"] == "no_comparable_observations_available"
    assert result["source"]["row_count"] == 0


def test_inconsistent_geometry_between_observations_is_rejected(reference_setup):
    _, scene = reference_setup
    first = _observation(0.1)
    second = _observation(0.1)
    second["geometry"]["surface_finish"] = "rough measured surface"
    request = ComparisonRequest.model_validate(
        {
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic CSV fixture for compatibility checks",
            "source_locator": "test fixture",
            "source_sha256": CSV_SHA256,
            "observations": [first, second],
        }
    )
    with pytest.raises(ValueError, match="geometry is inconsistent"):
        compare_observations(reference_setup[0], request)


def test_inconsistent_conditions_between_observations_are_rejected(reference_setup):
    _, scene = reference_setup
    first = _observation(0.1)
    second = _observation(0.1)
    second["conditions"]["temperature_k"] = 310.15
    request = ComparisonRequest.model_validate(
        {
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic CSV fixture for compatibility checks",
            "source_locator": "test fixture",
            "source_sha256": CSV_SHA256,
            "observations": [first, second],
        }
    )
    with pytest.raises(ValueError, match="conditions are inconsistent"):
        compare_observations(reference_setup[0], request)


def test_mismatched_incidence_rejected(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(0.1, angle=45)],
        },
    )
    assert response.status_code == 422
    assert "angle" in response.json()["detail"]


def test_hemispherical_values_not_falsely_compared(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(0.1, type_="hemispherical_reflectance")],
        },
    )
    assert response.status_code == 422


def test_emittance_not_supported(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(0.1, type_="emittance")],
        },
    )
    assert response.status_code == 422


def test_unavailable_is_explicit_when_no_legal_comparable_data(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "touloukian",
            "source_reference": "Touloukian radiative properties bibliography",
            "source_locator": "volume 7, candidate tables not redistributed",
            "observations": [],
            "unavailable_reason": (
                "No legally redistributable specular observation with matching angle "
                "and polarization is available in this checkout."
            ),
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "unavailable"
    assert response.json()["metrics"] is None
    assert response.json()["verification_status"] == "no_comparable_observations_available"


def test_csv_provenance_requires_sha256_and_source_row(reference_setup):
    _, scene = reference_setup
    payload = {
        "scene": scene.model_dump(),
        "source_kind": "csv",
        "source_reference": "Synthetic test-only CSV fixture",
        "source_locator": "test fixture, generated in test_validation.py",
        "observations": [_observation(0.1)],
    }
    payload["observations"][0].pop("source_row")
    response = TestClient(app).post("/api/v1/validation/compare", json=payload)
    assert response.status_code == 422
    assert "source_sha256" in response.text or "source_row" in response.text


def test_incompatible_surface_geometry_is_rejected(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(0.1, surface_finish_class="rough")],
        },
    )
    assert response.status_code == 422
    assert "surface" in response.json()["detail"].lower()


def test_incompatible_atmosphere_is_rejected(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [_observation(0.1, atmosphere="vacuum")],
        },
    )
    assert response.status_code == 422
    assert "atmosphere" in response.json()["detail"].lower()


def test_mixed_measurement_conditions_are_rejected(reference_setup):
    _, scene = reference_setup
    response = TestClient(app).post(
        "/api/v1/validation/compare",
        json={
            "scene": scene.model_dump(),
            "source_kind": "csv",
            "source_reference": "Synthetic test-only CSV fixture",
            "source_locator": "test fixture, generated in test_validation.py",
            "source_sha256": CSV_SHA256,
            "observations": [
                _observation(0.1, source_row=2),
                _observation(0.1, temperature_k=300.0, source_row=3),
            ],
        },
    )
    assert response.status_code == 422
    assert "temperature" in response.json()["detail"].lower()
