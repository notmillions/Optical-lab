# Optical Studio — Sprint S0

React 19, TypeScript, Vite 6 and React Three Fiber 9 with a configurable **illustrative** slab stack. Users can choose a source type, change incidence and polarization, add/reorder/remove layers and adjust display thicknesses.

This preview contains **no computed optical properties**. Materials are labeled for concept visualization only, not connected to RefractiveIndex.INFO until S1. TMM outputs arrive in S2.

```bash
cd apps/web
npm install
npm run dev
npm run typecheck
npm test
npm run build
```

Run the backend separately; Vite proxies `/api` to localhost:8000. See `docs/S0_SETUP.md`.

## Vercel

The Vite frontend can be deployed separately with `apps/web` as the Vercel
Root Directory, `npm run build` as the build command and `dist` as the output
directory. Set `VITE_API_BASE_URL` to the public FastAPI origin; otherwise the
deployed browser will show **BACKEND NON CONFIGURÉ** and will not claim that the
API is connected. See
[`docs/DEPLOYMENT_VERCEL.md`](../../docs/DEPLOYMENT_VERCEL.md).

## Environment contract

- `VITE_API_BASE_URL`: build-time frontend variable. Empty is valid only in
  local Vite development, where `/api` is proxied to `127.0.0.1:8000`. A
  deployed build requires an absolute `http://` or `https://` origin.
- `OPTICAL_LAB_WEB_ORIGINS`: backend runtime variable, not exposed to Vite.
  Set it to the exact Vercel origin, for example
  `https://optical-lab-web.vercel.app`, with comma-separated origins if more
  than one frontend is authorized. Do not include a path or wildcard.

The frontend smoke tests cover the health/capabilities handshake, the material
catalog, simulation and reproducible export routes:

```bash
npm test -- --run src/lib/api.test.ts
```
