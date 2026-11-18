/** Frontend contracts for the real Optical Lab HTTP service. */

import type { Polarization, PreviewLayer, SourceType } from "./scene";

export type MaterialDataset = {
  id: string;
  material_id: string;
  page: string;
  source_commit: string;
  source_path: string;
  references: string;
  doi_urls: string[];
  notes: string;
  has_n: boolean;
  has_k: boolean;
  min_nm: number;
  max_nm: number;
};

export type MaterialCatalogEntry = {
  id: string;
  name: string;
  dataset_count: number;
  datasets: MaterialDataset[];
};

export type MaterialCatalog = {
  materials: MaterialCatalogEntry[];
};

export type SimulationPoint = {
  wavelength_nm: number;
  polarization: string;
  reflectance: number;
  transmittance: number;
  absorptance: number;
  finite_layer_absorption: number[];
  exit_medium_absorption: number | null;
  interpretation: string;
};

export type SimulationOutput = {
  status: "computed";
  scene_schema_version: string;
  solver: string;
  points: SimulationPoint[];
  note: string;
  units: { wavelength: string; R: string; T: string; A: string };
  warnings?: string[];
  source?: Record<string, unknown>;
  incidence?: Record<string, unknown>;
  layers?: Array<Record<string, unknown>>;
  exit_dataset?: string;
  dataset_provenance: MaterialDataset[];
  source_weighted: null | {
    effective_R: number;
    effective_T: number;
    effective_A: number;
    reference_coverage: number;
    covered_wavelength_nm: [number, number];
    weight_units: string;
    source_reference: string;
    assumption: string;
    interpretation: string;
  };
};

export type ApiConfig = {
  baseUrl: string;
  configured: boolean;
  mode: "remote" | "local-proxy" | "missing" | "invalid";
};

export type BackendHealth = {
  status: string;
  stage: string;
};

export type BackendCapabilities = {
  stage: string;
  optical_solver: boolean;
  [key: string]: unknown;
};

/** Resolve environment configuration without silently treating a production build as local. */
export function resolveApiConfig(rawBaseUrl: string | undefined, isDev: boolean): ApiConfig {
  const baseUrl = (rawBaseUrl ?? "").trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return { baseUrl: "", configured: isDev, mode: isDev ? "local-proxy" : "missing" };
  }
  try {
    const parsed = new URL(baseUrl);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return { baseUrl, configured: true, mode: "remote" };
    }
  } catch {
    // The caller receives an explicit invalid configuration state below.
  }
  return { baseUrl, configured: false, mode: "invalid" };
}

const API_CONFIG = resolveApiConfig(import.meta.env.VITE_API_BASE_URL, import.meta.env.DEV);

export function getApiConfig(): ApiConfig {
  return API_CONFIG;
}

/** Resolve API routes for local Vite proxying or a separately deployed backend. */
export function apiUrl(path: string): string {
  if (!path.startsWith("/")) throw new Error("API paths must be absolute");
  if (!API_CONFIG.configured) {
    throw new Error(
      API_CONFIG.mode === "invalid"
        ? "URL du backend invalide : utilise une origine HTTP(S) dans VITE_API_BASE_URL."
        : "Backend non configuré : renseigne VITE_API_BASE_URL pour cette version déployée."
    );
  }
  return `${API_CONFIG.baseUrl}${path}`;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(apiUrl(url), { signal });
  if (!response.ok) {
    throw new Error(
      response.status === 503
        ? "Base non initialisée : exécute python -m packages.material_data dans le dépôt."
        : `API matériaux HTTP ${response.status}`
    );
  }
  return response.json() as Promise<T>;
}

export async function checkBackend(signal?: AbortSignal): Promise<{
  health: BackendHealth;
  capabilities: BackendCapabilities;
}> {
  const [health, capabilities] = await Promise.all([
    getJson<BackendHealth>("/api/v1/health", signal),
    getJson<BackendCapabilities>("/api/v1/capabilities", signal),
  ]);
  if (health.status !== "ok") throw new Error("API backend non saine.");
  return { health, capabilities };
}

export async function getCatalog(signal?: AbortSignal): Promise<MaterialCatalog> {
  return getJson<MaterialCatalog>("/api/v1/materials/catalog", signal);
}

/** Resolve a layer's backend material, including the pre-catalog SiO₂ label. */
export function materialForLayer(
  layer: PreviewLayer,
  catalog: MaterialCatalog
): MaterialCatalogEntry | undefined {
  return catalog.materials.find((material) =>
    material.id === layer.material
      || material.name === layer.material
      || (layer.material === "SiO₂" && material.id === "SiO2")
  );
}

export function datasetForLayer(
  layer: PreviewLayer,
  catalog: MaterialCatalog
): MaterialDataset {
  const material = materialForLayer(layer, catalog);
  const available = material?.datasets ?? [];
  const match = layer.datasetId
    ? available.find((dataset) => dataset.id === layer.datasetId)
    : available.find((dataset) => dataset.has_n && dataset.has_k);
  if (!material) throw new Error(`Matériau absent du catalogue : ${layer.material}`);
  if (!match) throw new Error(`Aucun jeu de données optique complet pour ${material.name}`);
  if (!match.has_n || !match.has_k) {
    throw new Error(`${material.name} — ${match.page} ne fournit pas n ET k. Sélectionne une autre référence.`);
  }
  return match;
}

export function buildScene(
  layers: PreviewLayer[],
  catalog: MaterialCatalog,
  source: SourceType,
  wavelengthNm: number,
  angleDeg: number,
  polarization: Polarization
): object {
  if (layers.length < 2) throw new Error("Il faut au moins une couche finie et un substrat.");
  const resolved = layers.map((layer) => ({
    layer,
    dataset: datasetForLayer(layer, catalog)
  }));
  return {
    schema_version: "1.0",
    kind: "planar-stack",
    source: source === "laser"
      ? { type: "laser", wavelength_nm: wavelengthNm }
      : source === "solar"
        ? { type: "solar", spectrum_id: "ASTM-G173-global" }
        : { type: "lamp", spectrum_id: "incandescent-2856K-planck" },
    incidence: { angle_deg: angleDeg, polarization },
    environment: {
      incident_medium: "air",
      exit_medium_dataset_id: resolved[resolved.length - 1].dataset.id
    },
    layers: resolved.slice(0, -1).map(({ layer, dataset }) => ({
      id: layer.id,
      dataset_id: dataset.id,
      thickness_nm: layer.thicknessNm,
      coherence: "coherent"
    })),
    solver: "planar-tmm"
  };
}

export async function runSimulation(
  scene: object,
  signal?: AbortSignal
): Promise<SimulationOutput> {
  const response = await fetch(apiUrl("/api/v1/simulations"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scene }),
    signal
  });
  if (!response.ok) {
    const data: unknown = await response.json().catch(() => null);
    const message =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `HTTP ${response.status}`;
    throw new Error(message);
  }
  return response.json() as Promise<SimulationOutput>;
}

export async function exportSimulation(
  scene: object,
  result: SimulationOutput | Record<string, unknown>,
  format: "json" | "csv"
): Promise<unknown> {
  const response = await fetch(apiUrl("/api/v1/exports"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scene, result, format }),
  });
  if (!response.ok) {
    const data: unknown = await response.json().catch(() => null);
    const message =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `HTTP ${response.status}`;
    throw new Error(message);
  }
  return format === "csv" ? response.text() : response.json();
}

export function representativeValues(result: SimulationOutput) {
  if (result.source_weighted) {
    const { effective_R, effective_T, effective_A } = result.source_weighted;
    return [effective_R, effective_T, effective_A] as const;
  }
  const p = result.points[0];
  return [p.reflectance, p.transmittance, p.absorptance] as const;
}
