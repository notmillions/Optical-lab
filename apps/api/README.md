# API Optical Lab — Sprint S0

FastAPI/Pydantic exposes `GET /api/v1/health`, `GET /api/v1/capabilities`, and `POST /api/v1/scenes/validate`. The validation route only checks schema and local constraints; it does not resolve real optical datasets or run TMM.

Run from repository root:

```bash
python -m pip install -e '.[dev]'
python -m uvicorn apps.api.main:app --reload
```

See `docs/S0_SETUP.md`. The optical simulation endpoints are reserved for future phases and are deliberately not exposed as working yet.
