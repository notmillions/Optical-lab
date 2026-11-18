"""Independent QA contracts for the split API/frontend deployment.

These tests intentionally do not import or manufacture optical data. They only
protect deployment assumptions that can be checked at the HTTP boundary.
"""

from fastapi.testclient import TestClient

from apps.api.main import app


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
