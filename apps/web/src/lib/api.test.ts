import { describe, expect, it, vi } from "vitest";

import {
  buildScene,
  checkBackend,
  datasetForLayer,
  exportSimulation,
  getCatalog,
  representativeValues,
  resolveApiConfig,
  runSimulation,
} from "./api";
import type { MaterialCatalog, SimulationOutput } from "./api";
import { INITIAL_LAYERS } from "./scene";

const datasets: MaterialCatalog = {
  materials: [
    {
      id: "SiO2",
      name: "Fused silica / silica",
      dataset_count: 2,
      datasets: [
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
    },
    {
      id: "Cu",
      name: "Copper",
      dataset_count: 1,
      datasets: [{
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
    },
    {
      id: "Al",
      name: "Aluminium",
      dataset_count: 1,
      datasets: [{
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
    },
    {
      id: "Au",
      name: "Gold",
      dataset_count: 1,
      datasets: [{
        id: "main:Au:nk:Johnson",
        material_id: "Au",
        page: "Johnson",
        source_commit: "snapshot",
        source_path: "Au/nk/Johnson.yml",
        references: "Johnson & Christy",
        doi_urls: [],
        notes: "",
        has_n: true,
        has_k: true,
        min_nm: 187,
        max_nm: 1937,
      }],
    },
  ],
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

describe("frontend/backend connection contract", () => {
  it("marks a missing production URL as unconfigured", () => {
    expect(resolveApiConfig(undefined, false)).toEqual({
      baseUrl: "",
      configured: false,
      mode: "missing",
    });
  });

  it("uses the Vite local proxy when development has no backend URL", () => {
    expect(resolveApiConfig(undefined, true)).toEqual({
      baseUrl: "",
      configured: true,
      mode: "local-proxy",
    });
  });

  it("rejects a non-http backend URL", () => {
    expect(resolveApiConfig("/api", false)).toEqual({
      baseUrl: "/api",
      configured: false,
      mode: "invalid",
    });
  });

  it("smoke-checks health and capabilities together", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/health")) {
        return new Response(JSON.stringify({ status: "ok", stage: "V1-partial" }), { status: 200 });
      }
      return new Response(JSON.stringify({ stage: "V1-partial", optical_solver: true }), { status: 200 });
    });

    await expect(checkBackend()).resolves.toEqual({
      health: { status: "ok", stage: "V1-partial" },
      capabilities: { stage: "V1-partial", optical_solver: true },
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    fetchMock.mockRestore();
  });

  it("smoke-checks catalog, simulation and reproducible export routes", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/materials/catalog")) {
        return new Response(JSON.stringify(datasets), { status: 200 });
      }
      if (url.endsWith("/simulations")) {
        return new Response(JSON.stringify({ status: "computed", points: [] }), { status: 200 });
      }
      expect(url).toContain("/exports");
      expect(init?.method).toBe("POST");
      return new Response(JSON.stringify({ export_schema_version: "1.0" }), { status: 200 });
    });

    await expect(getCatalog()).resolves.toEqual(datasets);
    await expect(runSimulation({ scene: "fixture" })).resolves.toMatchObject({ status: "computed" });
    await expect(exportSimulation({ scene: "fixture" }, { points: [] }, "json"))
      .resolves.toEqual({ export_schema_version: "1.0" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0][0]).toContain("/materials/catalog");
    fetchMock.mockRestore();
  });

  it("keeps backend material ids and datasets for materials beyond the pilot", () => {
    const gold = datasets.materials.find((material) => material.id === "Au");
    expect(gold?.name).toBe("Gold");
    expect(gold?.datasets[0].id).toBe("main:Au:nk:Johnson");
  });
});
