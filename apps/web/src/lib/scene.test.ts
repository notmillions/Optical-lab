import { describe, expect, it } from "vitest";

import {
  INITIAL_LAYERS,
  formatWavelength,
  moveLayer,
  updateLayerThickness
} from "./scene";

describe("preview scene state", () => {
  it("reorders layers without mutating source state", () => {
    const moved = moveLayer(INITIAL_LAYERS, 0, 1);
    expect(moved.map((layer) => layer.material)).toEqual(["Cu", "SiO₂"]);
    expect(INITIAL_LAYERS[0].material).toBe("SiO₂");
  });

  it("ignores an invalid move", () => {
    expect(moveLayer(INITIAL_LAYERS, 0, -1)).toBe(INITIAL_LAYERS);
  });

  it("updates positive thickness only", () => {
    expect(updateLayerThickness(INITIAL_LAYERS, "layer-1", 145)[0].thicknessNm)
      .toBe(145);
    expect(updateLayerThickness(INITIAL_LAYERS, "layer-1", -1))
      .toBe(INITIAL_LAYERS);
  });

  it("formats wavelengths for display only", () => {
    expect(formatWavelength(532)).toBe("532 nm");
  });
});
