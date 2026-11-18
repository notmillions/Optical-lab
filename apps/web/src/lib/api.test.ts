import { describe, expect, it } from "vitest";

import { buildScene, datasetForLayer, representativeValues } from "./api";
import type { MaterialCatalog, SimulationOutput } from "./api";
import { INITIAL_LAYERS } from "./scene";

const datasets: MaterialCatalog = {
  "SiO₂": [
    {
      id: "main:SiO2:nk:Gao",
      page: "Gao",
      material_id: "SiO2",
      source_commit: "snapshot",
      source_path: "SiO2/nk/Gao.yml",
      references: "Gao et al.",
      doi_urls: [],
      notes: "",
      has_n: true,
      has_k: true,
      min_nm: 252,
      max_nm: 1250,
    },
    {
      id: "main:SiO2:nk:Malitson",
      page: "Malitson",
      material_id: "SiO2",
      source_commit: "snapshot",
      source_path: "SiO2/nk/Malitson.yml",
      references: "Malitson",
      doi_urls: [],
      notes: "",
      has_n: true,
      has_k: false,
      min_nm: 210,
      max_nm: 6700,
    },
  ],
  Cu: [{
    id: "main:Cu:nk:Johnson",
    page: "Johnson",
    material_id: "Cu",
    source_commit: "snapshot",
    source_path: "Cu/nk/Johnson.yml",
    references: "Johnson & Christy",
    doi_urls: [],
    notes: "",
    has_n: true,
    has_k: true,
    min_nm: 187,
    max_nm: 1937,
  }],
  Al: [{
    id: "main:Al:nk:Rakic",
    page: "Rakic",
    material_id: "Al",
    source_commit: "snapshot",
    source_path: "Al/nk/Rakic.yml",
    references: "Rakic",
    doi_urls: [],
    notes: "",
    has_n: true,
    has_k: true,
    min_nm: 0.12,
    max_nm: 200000,
  }],
};

describe("scientific scene builder", () => {
  it("sends one finite layer and the last entry as semi-infinite substrate", () => {
    const payload = buildScene(INITIAL_LAYERS, datasets, "laser", 532, 30, "s") as {
      environment: { exit_medium_dataset_id: string };
      layers: { dataset_id: string; thickness_nm: number }[];
      source: { type: string; wavelength_nm: number };
    };
    expect(payload.environment.exit_medium_dataset_id).toBe("main:Cu:nk:Johnson");
    expect(payload.layers).toHaveLength(1);
    expect(payload.layers[0].dataset_id).toBe("main:SiO2:nk:Gao");
    expect(payload.layers[0].thickness_nm).toBe(100);
    expect(payload.source).toEqual({ type: "laser", wavelength_nm: 532 });
  });

  it("preserves physically documented spectral identifiers", () => {
    const payload = buildScene(INITIAL_LAYERS, datasets, "solar", 532, 30, "s") as {
      source: { spectrum_id: string };
    };
    expect(payload.source.spectrum_id).toBe("ASTM-G173-global");
  });

  it("never silently replaces missing k", () => {
    const first = { ...INITIAL_LAYERS[0], datasetId: "main:SiO2:nk:Malitson" };
    expect(() => datasetForLayer(first, datasets)).toThrow("n ET k");
  });

  it("uses source-weighted broadband values when supplied", () => {
    const result = {
      points: [{ reflectance: 0.1, transmittance: 0.8, absorptance: 0.1 }],
      source_weighted: { effective_R: 0.2, effective_T: 0.7, effective_A: 0.1 },
    } as SimulationOutput;
    expect(representativeValues(result)).toEqual([0.2, 0.7, 0.1]);
  });
});
