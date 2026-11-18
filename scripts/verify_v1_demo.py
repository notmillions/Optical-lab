"""Reproducible vertical-slice smoke with four REAL pinned optical datasets.

Run after scripts/verify_s1_pilots.py populated data/processed/s1-integration.sqlite.
All assertions operate on actual RefractiveIndex.INFO references, not dummy values.
"""

import os
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.models import OpticalScene
from packages.material_data.store import dataset_details
from packages.optical_core.broadband import aggregate_source
from packages.optical_core.solver import simulate_laser


def scene(source: dict) -> OpticalScene:
    return OpticalScene.model_validate({
        "schema_version": "1.0",
        "kind": "planar-stack",
        "source": source,
        "incidence": {"angle_deg": 30, "polarization": "s"},
        "environment": {
            "incident_medium": "air",
            "exit_medium_dataset_id": "main:Cu:nk:Johnson",
        },
        "layers": [{
            "id": "silica",
            "dataset_id": "main:SiO2:nk:Gao",
            "thickness_nm": 100,
            "coherence": "coherent",
        }],
        "solver": "planar-tmm",
    })


def main() -> None:
    db = Path("data/processed/s1-integration.sqlite")
    if not db.exists():
        raise RuntimeError("Import the pinned RefractiveIndex.INFO pilots first")

    laser = scene({"type": "laser", "wavelength_nm": 532})
    calculation = simulate_laser(str(db), laser)
    assert 0 <= calculation.reflectance <= 1
    assert 0 <= calculation.transmittance <= 1
    assert abs(calculation.reflectance + calculation.transmittance + calculation.absorptance - 1) < 1e-9
    assert len(calculation.finite_layer_absorption) == 1
    assert calculation.exit_medium_absorption is not None

    for dataset_id in ("main:SiO2:nk:Gao", "main:Cu:nk:Johnson"):
        details = dataset_details(db, dataset_id)
        assert details["has_n"] and details["has_k"]
        assert details["references"]
        assert details["source_sha256"]

    for kind, identifier in [
        ("solar", "ASTM-G173-global"),
        ("lamp", "incandescent-2856K-planck"),
    ]:
        response = aggregate_source(
            str(db), scene({"type": kind, "spectrum_id": identifier}),
            max_wavelengths=40
        )
        assert 0 < response.reference_coverage <= 1
        assert abs(response.effective_r + response.effective_t + response.effective_a - 1) < 1e-8
        print(
            f"{identifier}: R={response.effective_r:.5f} "
            f"T={response.effective_t:.5f} A={response.effective_a:.5f}, "
            f"source coverage={response.reference_coverage:.3f}"
        )

    os.environ["OPTICAL_LAB_DB"] = str(db)
    client = TestClient(app)
    result = client.post("/api/v1/simulations", json={"scene": laser.model_dump()})
    assert result.status_code == 200, result.text
    assert len(result.json()["dataset_provenance"]) == 2
    assert result.json()["points"][0]["reflectance"] == calculation.reflectance
    print("PASS: real pilot materials -> physical TMM -> API + references -> solar/lamp")


if __name__ == "__main__":
    main()
