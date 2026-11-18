"""Optical Lab API — material catalog and S2 physically calculated laser stacks."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.exports import router as exports_router
from apps.api.materials import router as materials_router
from apps.api.models import OpticalScene, SceneValidation
from apps.api.simulations import router as simulations_router
from apps.api.validation import router as validation_router

app = FastAPI(
    title="Optical Lab API",
    version="0.1.0",
    description="Foundational API contracts; scientific simulation arrives in S2.",
)
app.include_router(materials_router)
app.include_router(simulations_router)
app.include_router(validation_router)
app.include_router(exports_router)
_local_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_configured_origins = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("OPTICAL_LAB_WEB_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[*_local_origins, *_configured_origins],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "stage": "S3"}


@app.get("/api/v1/capabilities", tags=["system"])
def capabilities() -> dict[str, object]:
    return {
        "stage": "V1-partial",
        "scene_validation": True,
        "material_catalog": True,
        "material_import_required": True,
        "optical_solver": True,
        "supported_geometry": ["planar-stack"],
        "supported_solver_contracts": ["planar-tmm"],
        "solver_sources_supported": ["laser", "solar", "lamp"],
        "exports": ["json", "csv"],
        "experimental_comparison": "traceable-observations-or-unavailable",
    }


@app.post("/api/v1/scenes/validate", response_model=SceneValidation, tags=["scenes"])
def validate_scene(scene: OpticalScene) -> SceneValidation:
    return SceneValidation(
        valid=True,
        schema_version=scene.schema_version,
        layer_count=len(scene.layers),
        warning="Syntax validated only. Optical datasets and TMM solver are not installed yet.",
    )
