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
deployed browser will have no `/api` service. See
[`docs/DEPLOYMENT_VERCEL.md`](../../docs/DEPLOYMENT_VERCEL.md).
