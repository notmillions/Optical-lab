/** Frontend contracts for the real Optical Lab HTTP service. */

import type { Polarization, PreviewLayer, PreviewMaterial, SourceType } from "./scene";

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

export type MaterialCatalog = Record<PreviewMaterial, MaterialDataset[]>;

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

const BACKEND_ID: Record<PreviewMaterial, string> = {
  "SiO₂": "SiO2",
  Cu: "Cu",
  Al: "Al"
};

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(
      response.status === 503
        ? "Base non initialisée : exécute python -m packages.material_data dans le dépôt."
        : `API matériaux HTTP ${response.status}`
    );
  }
  return response.json() as Promise<T>;
}

export async function getCatalog(signal?: AbortSignal): Promise<MaterialCatalog> {
  const choices: PreviewMaterial[] = ["SiO₂", "Cu", "Al"];
  const all = await Promise.all(choices.map(async (material) => {
    const datasets = await getJson<MaterialDataset[]>(
      `/api/v1/materials/${BACKEND_ID[material]}/datasets`,
      signal
    );
    return [material, datasets] as const;
  }));
  return Object.fromEntries(all) as MaterialCatalog;
}

export function datasetForLayer(
  layer: PreviewLayer,
  catalog: MaterialCatalog
): MaterialDataset {
  const available = catalog[layer.material];
  const match = layer.datasetId
    ? available.find((dataset) => dataset.id === layer.datasetId)
    : available.find((dataset) => dataset.has_n && dataset.has_k);
  if (!match) throw new Error(`Aucun jeu de données optique complet pour ${layer.material}`);
  if (!match.has_n || !match.has_k) {
    throw new Error(
      `${layer.material} — ${match.page} ne fournit pas n ET k. Sélectionne une autre référence.`
    );
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
  const response = await fetch("/api/v1/simulations", {
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

export function representativeValues(result: SimulationOutput) {
  if (result.source_weighted) {
    const { effective_R, effective_T, effective_A } = result.source_weighted;
    return [effective_R, effective_T, effective_A] as const;
  }
  const p = result.points[0];
  return [p.reflectance, p.transmittance, p.absorptance] as const;
}
