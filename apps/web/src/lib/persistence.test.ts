import { describe, expect, it } from "vitest";
import { loadScene, saveScene, serializeExport, serializeScene, simulationCsv, validateScene } from "./persistence";
import type { SimulationOutput } from "./api";

const base = {
  source: "laser" as const,
  wavelength_nm: 532,
  angle_deg: 30,
  polarization: "s" as const,
  layers: [
    { id: "l1", material: "SiO₂" as const, datasetId: "main:SiO2:nk:Gao", thicknessNm: 100 },
    { id: "l2", material: "Cu" as const, datasetId: "main:Cu:nk:Johnson", thicknessNm: 80 },
  ],
};

describe("scene persistence", () => {
  function storage(): Storage {
    const values = new Map<string, string>();
    return {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => { values.set(key, value); },
      removeItem: (key) => { values.delete(key); },
      clear: () => { values.clear(); },
      key: (index) => [...values.keys()][index] ?? null,
      get length() { return values.size; }
    };
  }

  it("saves and reloads the validated scene from versioned storage", () => {
    const store = storage();
    const saved = saveScene(base, store);
    expect(loadScene(store)).toEqual(saved);
  });

  it("roundtrips a versioned scene", () => {
    const parsed = validateScene(JSON.parse(serializeScene(base)));
    expect(parsed.schema_version).toBe("1.0");
    expect(parsed.layers).toEqual(base.layers);
    expect(parsed.source).toBe("laser");
    expect(parsed.kind).toBe("planar-stack");
    expect(parsed.solver).toBe("planar-tmm");
  });

  it("refuses unsupported geometry and unknown material", () => {
    const wrong = JSON.parse(serializeScene(base));
    wrong.schema_version = "2.0";
    expect(() => validateScene(wrong)).toThrow("Version");
    wrong.schema_version = "1.0";
    wrong.kind = "freeform";
    expect(() => validateScene(wrong)).toThrow("Type");
    wrong.kind = "planar-stack";
    wrong.layers[0].material = "Unobtanium";
    expect(() => validateScene(wrong)).toThrow("Couche");
  });

  it("rejects duplicate IDs", () => {
    const wrong = JSON.parse(serializeScene(base));
    wrong.layers[1].id = wrong.layers[0].id;
    expect(() => validateScene(wrong)).toThrow("Couche");
  });

  it("serializes CSV with provenance and guards against formula injection", () => {
    const result = {
      solver: "tmm",
      scene_schema_version: "1.0",
      units: { wavelength: "nm", R: "fraction", T: "fraction", A: "fraction" },
      points: [{
        wavelength_nm: 532,
        polarization: "s",
        reflectance: 0.2,
        transmittance: 0.6,
        absorptance: 0.2,
      }],
      dataset_provenance: [{
        id: "main:SiO2:nk:Gao",
        source_commit: "f".repeat(40),
        references: "=DANGEROUS",
      }],
      warnings: ["synthetic test warning"],
    } as SimulationOutput;
    const csv = simulationCsv(result);
    expect(csv).toContain("wavelength_nm");
    expect(csv).toContain("main:SiO2:nk:Gao");
    expect(csv).toContain("'=DANGEROUS");
    expect(csv).toContain("synthetic test warning");
    expect(csv).toContain("semi-infinite exit substrate");
    expect(csv).toContain('"0.2"');
    expect(csv.split("\r\n")).toHaveLength(3);
  });

  it("exports a reproducible JSON bundle with scene, units and interpretation", () => {
    const result = {
      solver: "tmm", scene_schema_version: "1.0",
      units: { wavelength: "nm", R: "fraction", T: "fraction", A: "fraction" },
      points: [], dataset_provenance: [], status: "computed", note: "T enters substrate",
      warnings: ["coverage limited"]
    } as unknown as SimulationOutput;
    const bundle = JSON.parse(serializeExport(base, result));
    expect(bundle.export_schema_version).toBe("1.0");
    expect(bundle.scene.layers).toHaveLength(2);
    expect(bundle.units).toEqual({ wavelength: "nm", fractions: "R/T/A" });
    expect(bundle.warnings).toEqual(["coverage limited"]);
    expect(bundle.interpretation).toContain("semi-infinite exit substrate");
  });
});
