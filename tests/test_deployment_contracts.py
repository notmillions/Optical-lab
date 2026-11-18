"""Independent QA contracts for the split API/frontend deployment.

These tests exercise the deployment bootstrap with small synthetic source trees
and protect assumptions that can be checked at the HTTP boundary.
"""

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app
from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets, list_datasets, list_source_records

_START_API_PATH = Path(__file__).resolve().parents[1] / "scripts" / "start_api.py"
_START_API_SPEC = importlib.util.spec_from_file_location("optical_lab_start_api", _START_API_PATH)
assert _START_API_SPEC and _START_API_SPEC.loader
_START_API = importlib.util.module_from_spec(_START_API_SPEC)
_START_API_SPEC.loader.exec_module(_START_API)
ensure_catalogue = _START_API.ensure_catalogue


SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"


def _source_tree(root):
    supported = root / "database/data/main/Cu/nk/Johnson.yml"
    unsupported = root / "database/data/main/Cu/nk/unsupported.yml"
    invalid = root / "database/data/main/Cu/nk/invalid.yml"
    supported.parent.mkdir(parents=True)
    supported.write_text(
        "REFERENCES: Synthetic\n"
        "DATA:\n"
        "  - type: tabulated nk\n"
        "    data: |\n"
        "      0.4 1.5 0.1\n"
        "      0.6 1.6 0.2\n",
        encoding="utf-8",
    )
    unsupported.write_text(
        "REFERENCES: Synthetic\n"
        "DATA:\n"
        "  - type: formula 9\n"
        "    data: unknown\n",
        encoding="utf-8",
    )
    invalid.write_text(
        "REFERENCES: Synthetic\n"
        "DATA:\n"
        "  - type: tabulated nk\n"
        "    data: |\n"
        "      0.4 1.5\n",
        encoding="utf-8",
    )


def test_bootstrap_imports_full_source_tree_and_keeps_manifest_statuses(tmp_path):
    database = tmp_path / "catalog.sqlite"
    source_root = tmp_path / "snapshot"
    marker = tmp_path / "catalog-bootstrap.json"
    _source_tree(source_root)

    count = ensure_catalogue(database, source_root=source_root, marker=marker)

    assert count == 1
    assert len(list_datasets(database)) == 1
    assert [row["status"] for row in list_source_records(database)] == [
        "imported",
        "invalid",
        "unsupported",
    ]
    assert marker.is_file()


def test_bootstrap_upgrades_nonempty_pilot_database_and_is_idempotent(tmp_path):
    database = tmp_path / "catalog.sqlite"
    source_root = tmp_path / "snapshot"
    marker = tmp_path / "catalog-bootstrap.json"
    _source_tree(source_root)
    pilot = parse_dataset(
        "database/data/main/Cu/nk/Johnson.yml",
        (source_root / "database/data/main/Cu/nk/Johnson.yml").read_bytes(),
        SNAPSHOT,
    )
    import_datasets(database, [pilot])

    assert ensure_catalogue(database, source_root=source_root, marker=marker) == 1

    (source_root / "database/data/main/Cu/nk/Johnson.yml").write_text(
        "this must not be read after the marker is committed\n", encoding="utf-8"
    )
    assert ensure_catalogue(database, source_root=source_root, marker=marker) == 1
    assert len(list_source_records(database)) == 3


def test_health_is_a_liveness_contract_only() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stage": "S3"}


def test_catalog_reports_uninitialized_database_as_service_unavailable(
    tmp_path, monkeypatch
) -> None:
    missing_database = tmp_path / "not-initialized.sqlite"
    monkeypatch.setenv("OPTICAL_LAB_DB", str(missing_database))

    response = TestClient(app).get("/api/v1/materials")

    assert response.status_code == 503
    assert "not initialized" in response.json()["detail"]


def test_cors_allows_local_frontend_origin() -> None:
    response = TestClient(app).options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_does_not_allow_an_arbitrary_origin() -> None:
    response = TestClient(app).options(
        "/api/v1/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
