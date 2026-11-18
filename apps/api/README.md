# API Optical Lab — Sprint S0

FastAPI/Pydantic exposes health/capabilities, material catalog, TMM simulation,
validation and reproducible export routes. `GET /api/v1/health` is the public
readiness probe used by the separately hosted Vercel frontend.

Run from repository root:

```bash
python -m pip install -e '.[dev]'
python -m uvicorn apps.api.main:app --reload
```

For a separately hosted frontend, configure the backend runtime before starting
it:

```dotenv
OPTICAL_LAB_DB=/persistent/path/optical-lab.sqlite
OPTICAL_LAB_WEB_ORIGINS=https://optical-lab-web.vercel.app
```

`OPTICAL_LAB_WEB_ORIGINS` is a comma-separated allowlist of exact browser
origins. It must not be `*`; local `localhost:5173` and `127.0.0.1:5173`
origins remain allowed for development. Initialize `OPTICAL_LAB_DB` with the
authorized material snapshot before expecting catalog or simulation requests
to succeed.

See `docs/S0_SETUP.md` and `docs/DEPLOYMENT_VERCEL.md`.
