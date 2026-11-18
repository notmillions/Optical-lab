"""S3 broadband tests: physical source weighting and explicit spectral coverage."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.models import OpticalScene
from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets
from packages.optical_core.broadband import aggregate_source
from packages.optical_core.spectra import (
    get_spectrum,
    incandescent_reference,
    reference_sources,
    solar_reference,
)

SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"


@pytest.fixture
def broad_db(tmp_path, monkeypatch):
    db = tmp_path / "broad.sqlite"
    records = []
    # Synthetic constant optical indices solely for unit/integration tests.
    for name, n, k in (("WindowTest", 1.5, 0.0), ("AirTest", 1.0, 0.0)):
        src = f"""REFERENCES: "Synthetic source for numerical integration tests only"
DATA:
  - type: tabulated nk
    data: |
      0.380 {n} {k}
      0.580 {n} {k}
      0.780 {n} {k}
""".encode()
        records.append(parse_dataset(
            f"database/data/main/{name}/nk/Test.yml", src, SNAPSHOT
        ))
    import_datasets(db, records)
    monkeypatch.setenv("OPTICAL_LAB_DB", str(db))
    return str(db)


def scene(source_type: str, spectrum_id: str) -> OpticalScene:
    return OpticalScene.model_validate({
        "kind": "planar-stack",
        "schema_version": "1.0",
        "source": {"type": source_type, "spectrum_id": spectrum_id},
        "incidence": {"angle_deg": 0, "polarization": "unpolarized"},
        "environment": {
            "incident_medium": "air",
            "exit_medium_dataset_id": "main:AirTest:nk:Test",
        },
        "layers": [{
            "id": "film",
            "dataset_id": "main:WindowTest:nk:Test",
            "thickness_nm": 100,
            "coherence": "coherent",
        }],
        "solver": "planar-tmm",
    })


def test_documented_lamp_spectrum():
    lamp = incandescent_reference("incandescent-2856K-planck")
    assert lamp.kind == "lamp"
    assert lamp.wavelengths_nm[0] == 380
    assert lamp.wavelengths_nm[-1] == 780
    assert min(lamp.weights) > 0
    assert max(lamp.weights) == pytest.approx(1)
    assert "Planck" in lamp.reference
    with pytest.raises(ValueError):
        get_spectrum("lamp", "fake-spectra")


def test_astm_solar_spectrum_is_read_from_pvlib():
    source = solar_reference("ASTM-G173-global")
    assert source.wavelengths_nm[0] < 400
    assert source.wavelengths_nm[-1] > 1000
    assert all(w >= 0 for w in source.weights)
    assert source.units == "W m^-2 nm^-1"


def test_incandescent_weighted_power_conservation(broad_db):
    aggregate = aggregate_source(
        broad_db, scene("lamp", "incandescent-2856K-planck"), max_wavelengths=40
    )
    assert 0 <= aggregate.effective_r <= 1
    assert 0 <= aggregate.effective_t <= 1
    assert aggregate.effective_r + aggregate.effective_t + aggregate.effective_a == pytest.approx(1)
    assert aggregate.reference_coverage == pytest.approx(1)
    assert aggregate.covered_nm == (380, 780)


def test_solar_reports_partial_coverage(broad_db):
    aggregate = aggregate_source(
        broad_db, scene("solar", "ASTM-G173-global"), max_wavelengths=40
    )
    assert 0 < aggregate.reference_coverage < 1
    assert aggregate.effective_r + aggregate.effective_t + aggregate.effective_a == pytest.approx(1)
    assert aggregate.covered_nm[0] >= 380
    assert aggregate.covered_nm[1] <= 780


def test_source_api_and_lamp_calculation(broad_db):
    client = TestClient(app)
    catalog = client.get("/api/v1/simulations/sources")
    assert catalog.status_code == 200
    assert {x["type"] for x in catalog.json()} == {"laser", "solar", "lamp"}
    response = client.post(
        "/api/v1/simulations", json={
            "scene": scene("lamp", "incandescent-2856K-planck").model_dump()
        }
    )
    assert response.status_code == 200, response.text
    summary = response.json()["source_weighted"]
    assert 0 <= summary["effective_R"] <= 1
    assert "2856" in summary["source_reference"]
    assert summary["reference_coverage"] == pytest.approx(1)


def test_broadband_rejects_unsupported_identifier(broad_db):
    client = TestClient(app)
    invalid = scene("solar", "ASTM-G173-global").model_dump()
    invalid["source"]["spectrum_id"] = "unknown"
    res = client.post("/api/v1/simulations", json={"scene": invalid})
    assert res.status_code == 422


def test_spectral_grid_is_laser_only(broad_db):
    client = TestClient(app)
    res = client.post("/api/v1/simulations/spectral", json={
        "scene": scene("lamp", "incandescent-2856K-planck").model_dump(),
        "wavelengths_nm": [400, 500]
    })
    assert res.status_code == 422
