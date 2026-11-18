"""Scientific solver tests using explicitly synthetic optical datasets.

No test constants are presented to users as measured refractive indices.
"""

from math import pi

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.models import OpticalScene
from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets
from packages.optical_core.solver import (
    absorption_coefficient,
    interface_reflectance,
    scan_spectrum,
    simulate_laser,
    simulate_planar,
)

SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"


@pytest.fixture
def library(tmp_path, monkeypatch):
    db = tmp_path / "physics.sqlite"
    records = []
    for material, values in (
        ("GlassTest", ("1.5", "0")),
        ("AbsorberTest", ("2", "0.25")),
        ("AirTest", ("1", "0")),
    ):
        n, k = values
        sample = f"""REFERENCES: "Synthetic numerical solver test (not measured)"
DATA:
  - type: tabulated nk
    data: |
      0.400 {n} {k}
      0.532 {n} {k}
      0.700 {n} {k}
""".encode()
        records.append(parse_dataset(
            f"database/data/main/{material}/nk/Test.yml", sample, SNAPSHOT
        ))
    import_datasets(db, records)
    monkeypatch.setenv("OPTICAL_LAB_DB", str(db))
    return str(db)


def scene(
    polarization="s",
    layer="GlassTest",
    outgoing="AirTest",
    coherence="coherent",
    angle=0.0,
):
    return OpticalScene.model_validate({
        "schema_version": "1.0",
        "kind": "planar-stack",
        "source": {"type": "laser", "wavelength_nm": 532},
        "incidence": {"angle_deg": angle, "polarization": polarization},
        "environment": {
            "incident_medium": "air",
            "exit_medium_dataset_id": f"main:{outgoing}:nk:Test",
        },
        "layers": [{
            "id": "L1", "dataset_id": f"main:{layer}:nk:Test",
            "thickness_nm": 100, "coherence": coherence
        }],
        "solver": "planar-tmm",
    })


def test_fresnel_reference_at_normal_incidence():
    assert interface_reflectance(1.5, 0.0) == pytest.approx(0.04)
    assert interface_reflectance(1.0, 0.0) == pytest.approx(0)
    assert absorption_coefficient(0.1, 500) == pytest.approx(4 * pi * 0.1 / 5e-7)


def test_nonabsorbing_film_sums_to_one(library):
    s = simulate_laser(library, scene())
    p = simulate_laser(library, scene("p"))
    assert s.reflectance == pytest.approx(p.reflectance, abs=1e-10)
    assert s.transmittance == pytest.approx(p.transmittance, abs=1e-10)
    assert s.reflectance + s.transmittance + s.absorptance == pytest.approx(1)
    assert s.absorptance == pytest.approx(0, abs=1e-9)
    assert s.finite_layer_absorption[0] == pytest.approx(0, abs=1e-9)


def test_absorbing_film_has_positive_absorption(library):
    result = simulate_laser(library, scene(layer="AbsorberTest"))
    assert 0 < result.absorptance < 1
    assert result.finite_layer_absorption[0] == pytest.approx(result.absorptance)
    assert result.exit_medium_absorption is None


def test_incoherent_mode_supported(library):
    result = simulate_laser(library, scene(coherence="incoherent", layer="AbsorberTest"))
    assert result.absorptance > 0
    assert result.reflectance + result.transmittance + result.absorptance == pytest.approx(1)


def test_unpolarized_is_average(library):
    s = simulate_planar(library, scene(angle=40), 532, "s")
    p = simulate_planar(library, scene(angle=40), 532, "p")
    u = simulate_planar(library, scene("unpolarized", angle=40), 532, "unpolarized")
    assert u.reflectance == pytest.approx((s.reflectance + p.reflectance) / 2)
    assert u.transmittance == pytest.approx((s.transmittance + p.transmittance) / 2)


def test_spectral_scan_with_valid_points(library):
    result = scan_spectrum(library, scene(), [450, 532, 650])
    assert len(result) == 3
    assert all(0 <= row.reflectance <= 1 for row in result)


def test_spectrum_rejects_out_of_domain(library):
    with pytest.raises(ValueError):
        scan_spectrum(library, scene(), [])
    with pytest.raises(ValueError):
        scan_spectrum(library, scene(), [-1])
    with pytest.raises(ValueError):
        scan_spectrum(library, scene(), [900])


def test_tmm_api_is_real_and_rejects_unknown_datasets(library):
    client = TestClient(app)
    response = client.post("/api/v1/simulations", json={"scene": scene().model_dump()})
    assert response.status_code == 200, response.text
    values = response.json()["points"][0]
    assert values["reflectance"] + values["transmittance"] + values["absorptance"] == pytest.approx(1)
    spectral = client.post(
        "/api/v1/simulations/spectral",
        json={"scene": scene().model_dump(), "wavelengths_nm": [450, 532, 650]},
    )
    assert spectral.status_code == 200, spectral.text
    assert len(spectral.json()["points"]) == 3
    broken = scene().model_dump()
    broken["layers"][0]["dataset_id"] = "unknown"
    assert client.post("/api/v1/simulations", json={"scene": broken}).status_code == 404


def test_solar_requires_s3(library):
    client = TestClient(app)
    config = scene().model_dump()
    config["source"] = {"type": "solar", "spectrum_id": "ASTM-G173"}
    response = client.post("/api/v1/simulations", json={"scene": config})
    assert response.status_code == 422
    assert "S3" in response.json()["detail"]
