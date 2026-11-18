"""S0 API tests require no catalog and no physical solver."""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def example_scene() -> dict:
    # These are syntactic demo IDs, not measured optical datasets.
    return {
        "schema_version": "1.0",
        "kind": "planar-stack",
        "source": {"type": "laser", "wavelength_nm": 532},
        "incidence": {"angle_deg": 30, "polarization": "s"},
        "environment": {
            "incident_medium": "air",
            "exit_medium_dataset_id": "Cu/EXAMPLE",
        },
        "layers": [
            {
                "id": "film-1",
                "dataset_id": "SiO2/EXAMPLE",
                "thickness_nm": 100,
                "coherence": "coherent",
            }
        ],
        "solver": "planar-tmm",
    }


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stage": "S2"}


def test_capabilities_are_honest() -> None:
    result = client.get("/api/v1/capabilities").json()
    assert result["scene_validation"] is True
    assert result["optical_solver"] is True
    assert result["solver_sources_supported"] == ["laser"]
    assert result["material_catalog"] is True
    assert result["material_import_required"] is True


def test_validate_planar_scene() -> None:
    response = client.post("/api/v1/scenes/validate", json=example_scene())
    assert response.status_code == 200
    assert response.json()["layer_count"] == 1
    assert response.json()["warning"].startswith("Syntax validated only.")


def test_rejects_v2_geometry() -> None:
    scene = example_scene()
    scene["kind"] = "free-3d"
    assert client.post("/api/v1/scenes/validate", json=scene).status_code == 422


def test_rejects_invalid_layer_thickness() -> None:
    scene = example_scene()
    scene["layers"][0]["thickness_nm"] = -10
    assert client.post("/api/v1/scenes/validate", json=scene).status_code == 422


def test_rejects_invalid_angle() -> None:
    scene = example_scene()
    scene["incidence"]["angle_deg"] = 90
    assert client.post("/api/v1/scenes/validate", json=scene).status_code == 422


def test_rejects_duplicate_layer_ids() -> None:
    scene = example_scene()
    scene["layers"].append({**scene["layers"][0]})
    assert client.post("/api/v1/scenes/validate", json=scene).status_code == 422


def test_rejects_malformed_source() -> None:
    scene = example_scene()
    scene["source"] = {"type": "laser", "wavelength_nm": 0}
    assert client.post("/api/v1/scenes/validate", json=scene).status_code == 422
