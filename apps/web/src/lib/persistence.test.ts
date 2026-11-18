import { describe, expect, it } from "vitest";
import { serializeScene, simulationCsv, validateScene } from "./persistence";
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
  it("roundtrips a versioned scene", () => {
    const parsed = validateScene(JSON.parse(serializeScene(base)));
    expect(parsed.schema_version).toBe("1.0");
    expect(parsed.layers).toEqual(base.layers);
    expect(parsed.source).toBe("laser");
  });

  it("refuses unsupported geometry and unknown material", () => {
    const wrong = JSON.parse(serializeScene(base));
    wrong.schema_version = "2.0";
    expect(() => validateScene(wrong)).toThrow("Version");
    wrong.schema_version = "1.0";
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
    } as SimulationOutput;
    const csv = simulationCsv(result);
    expect(csv).toContain("wavelength_nm");
    expect(csv).toContain("main:SiO2:nk:Gao");
    expect(csv).toContain("'=DANGEROUS");
    expect(csv).toContain('"0.2"');
    expect(csv.split("\r\n")).toHaveLength(3);
  });
});
