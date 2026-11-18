/** Presentation-only scene state for S0, not measured optical data. */

export type SourceType = "laser" | "solar" | "lamp";
export type Polarization = "s" | "p" | "unpolarized";
export type PreviewMaterial = "SiO₂" | "Cu" | "Al";

export interface PreviewLayer {
  id: string;
  material: PreviewMaterial;
  datasetId?: string;
  thicknessNm: number;
}

export const INITIAL_LAYERS: PreviewLayer[] = [
  { id: "layer-1", material: "SiO₂", thicknessNm: 100 },
  { id: "layer-2", material: "Cu", thicknessNm: 80 }
];

export const SOURCE_LABEL: Record<SourceType, string> = {
  laser: "Laser",
  solar: "Soleil",
  lamp: "Lampe"
};

export function moveLayer(
  layers: PreviewLayer[],
  index: number,
  delta: -1 | 1
): PreviewLayer[] {
  const target = index + delta;
  if (index < 0 || index >= layers.length || target < 0 || target >= layers.length) {
    return layers;
  }
  const next = layers.slice();
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

export function updateLayerThickness(
  layers: PreviewLayer[],
  id: string,
  thicknessNm: number
): PreviewLayer[] {
  if (!Number.isFinite(thicknessNm) || thicknessNm <= 0) return layers;
  return layers.map((layer) =>
    layer.id === id ? { ...layer, thicknessNm } : layer
  );
}

export function formatWavelength(wavelengthNm: number): string {
  return `${wavelengthNm.toLocaleString("fr-FR")} nm`;
}
