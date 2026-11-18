"""Optical Lab API S0 — explicit capabilities, no fake optical calculations."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.models import OpticalScene, SceneValidation

app = FastAPI(
    title="Optical Lab API",
    version="0.1.0",
    description="Foundational API contracts; scientific simulation arrives in S2.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "S0"}


@app.get("/api/v1/capabilities", tags=["system"])
def capabilities() -> dict[str, object]:
    return {
        "stage": "S0",
        "scene_validation": True,
        "material_catalog": False,
        "optical_solver": False,
        "supported_geometry": ["planar-stack"],
        "supported_solver_contracts": ["planar-tmm"],
    }


@app.post("/api/v1/scenes/validate", response_model=SceneValidation, tags=["scenes"])
def validate_scene(scene: OpticalScene) -> SceneValidation:
    return SceneValidation(
        valid=True,
        schema_version=scene.schema_version,
        layer_count=len(scene.layers),
        warning="Syntax validated only. Optical datasets and TMM solver are not installed yet.",
    )
