"""S1 API tests: independent materials and explicit absent extinction."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets

SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    path = tmp_path / "materials.sqlite"
    fixture = b"""REFERENCES: "Synthetic test-only data, not a scientific record"
COMMENTS: "Tests only"
DATA:
  - type: tabulated n
    data: |
      0.4 1.5
      0.6 1.7
"""
    record = parse_dataset("database/data/main/SiO2/nk/synthetic.yml", fixture, SNAPSHOT)
    import_datasets(path, [record])
    monkeypatch.setenv("OPTICAL_LAB_DB", str(path))
    return TestClient(app)


def test_material_search(api_client):
    response = api_client.get("/api/v1/materials", params={"q": "SiO2"})
    assert response.status_code == 200
    assert response.json()[0]["dataset_count"] == 1


def test_reference_available(api_client):
    response = api_client.get("/api/v1/datasets/main:SiO2:nk:synthetic")
    assert response.status_code == 200
    assert "Synthetic" in response.json()["references"]
    assert response.json()["source_commit"] == SNAPSHOT


def test_n_only_evaluation_never_invents_k(api_client):
    response = api_client.get(
        "/api/v1/datasets/main:SiO2:nk:synthetic/evaluate",
        params={"wavelength_nm": 500},
    )
    assert response.status_code == 200
    assert response.json()["n"] == pytest.approx(1.6)
    assert response.json()["k"] is None
    assert not response.json()["complete_for_tmm"]


def test_require_nk_rejected(api_client):
    response = api_client.get(
        "/api/v1/datasets/main:SiO2:nk:synthetic/evaluate",
        params={"wavelength_nm": 500, "require_nk": "true"},
    )
    assert response.status_code == 422
    assert "k missing" in response.json()["detail"]


def test_missing_and_out_of_domain(api_client):
    assert api_client.get("/api/v1/datasets/absent").status_code == 404
    response = api_client.get(
        "/api/v1/datasets/main:SiO2:nk:synthetic/evaluate",
        params={"wavelength_nm": 800},
    )
    assert response.status_code == 422
