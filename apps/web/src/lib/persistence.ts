/** Reproducible user-side scene storage/export, separate from scientific calculation. */

import type { SimulationOutput } from "./api";
import type { Polarization, PreviewLayer, SourceType } from "./scene";

export const STORAGE_KEY = "optical-lab:scene:v1";

export type SavedScene = {
  schema_version: "1.0";
  saved_at: string;
  source: SourceType;
  wavelength_nm: number;
  angle_deg: number;
  polarization: Polarization;
  layers: PreviewLayer[];
};

const MATERIALS = ["SiO₂", "Cu", "Al"];
const SOURCES = ["laser", "solar", "lamp"];
const POLARIZATIONS = ["s", "p", "unpolarized"];

export function validateScene(value: unknown): SavedScene {
  if (!value || typeof value !== "object") throw new Error("Configuration JSON invalide");
  const o = value as Record<string, unknown>;
  if (o.schema_version !== "1.0") throw new Error("Version de scène incompatible");
  if (typeof o.saved_at !== "string") throw new Error("Date de sauvegarde manquante");
  if (!SOURCES.includes(o.source as string)) throw new Error("Source inconnue");
  if (!POLARIZATIONS.includes(o.polarization as string)) throw new Error("Polarisation inconnue");
  if (typeof o.wavelength_nm !== "number" || !Number.isFinite(o.wavelength_nm)
    || o.wavelength_nm <= 0) throw new Error("Longueur d'onde invalide");
  if (typeof o.angle_deg !== "number" || !Number.isFinite(o.angle_deg)
    || o.angle_deg < 0 || o.angle_deg >= 90) throw new Error("Angle invalide");
  if (!Array.isArray(o.layers) || o.layers.length < 2 || o.layers.length > 200)
    throw new Error("Une couche finie et un substrat au minimum sont nécessaires");
  const seen = new Set<string>();
  for (const layer of o.layers) {
    if (!layer || typeof layer !== "object"
      || typeof layer.id !== "string"
      || !layer.id || seen.has(layer.id)
      || !MATERIALS.includes(layer.material)
      || typeof layer.thicknessNm !== "number" || !Number.isFinite(layer.thicknessNm)
      || layer.thicknessNm <= 0
      || (layer.datasetId !== undefined && typeof layer.datasetId !== "string")) {
      throw new Error("Couche invalide, doublon ou matériau non reconnu");
    }
    seen.add(layer.id);
  }
  return o as SavedScene;
}

export function serializeScene(scene: Omit<SavedScene, "schema_version" | "saved_at">): string {
  return JSON.stringify({
    schema_version: "1.0",
    saved_at: new Date().toISOString(),
    ...scene
  } satisfies SavedScene, null, 2);
}

function csv(value: string | number | null | undefined): string {
  const content = String(value ?? "");
  // Quote all cells; prevent spreadsheet formula injection on export.
  const escaped = /^[=+@\-\t\r]/.test(content) ? "'" + content : content;
  return '"' + escaped.replace(/"/g, '""') + '"';
}

export function simulationCsv(result: SimulationOutput): string {
  const header = [
    "wavelength_nm", "polarization", "R", "T", "A",
    "solver", "source_datasets", "source_snapshots", "source_references"
  ];
  const ds = result.dataset_provenance || [];
  const ids = ds.map((item) => item.id).join("; ");
  const snapshots = ds.map((item) => item.source_commit).join("; ");
  const references = ds.map((item) => item.references.replace(/<[^>]+>/g, " ")).join("; ");
  const rows = result.points.map((p) => [
    p.wavelength_nm, p.polarization,
    p.reflectance, p.transmittance, p.absorptance,
    result.solver, ids, snapshots, references
  ].map(csv).join(","));
  return [header.map(csv).join(","), ...rows].join("\r\n") + "\r\n";
}

export function browserDownload(name: string, data: string, mime: string): void {
  const blob = new Blob([data], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
