import { describe, it, expect } from "vitest";
import {
  hviColor,
  HVI_COLORS,
  HVI_NO_DATA_COLOR,
  HVI_BIN_MAX,
} from "./hvi";

describe("hviColor", () => {
  it("returns no-data gray for null", () => {
    expect(hviColor(null)).toBe(HVI_NO_DATA_COLOR);
  });

  it("returns no-data gray for undefined", () => {
    expect(hviColor(undefined)).toBe(HVI_NO_DATA_COLOR);
  });

  it("returns no-data gray for NaN", () => {
    expect(hviColor(NaN)).toBe(HVI_NO_DATA_COLOR);
  });

  it("maps boundary value 0 to the lowest bin", () => {
    expect(hviColor(0)).toBe(HVI_COLORS[0]);
  });

  it("maps a value just below each bin boundary to the correct color", () => {
    // Bin 0 covers [0, 20), bin 1 covers [20, 35), etc.
    const cases: [number, string][] = [
      [19, HVI_COLORS[0]],
      [20, HVI_COLORS[1]],
      [34, HVI_COLORS[1]],
      [35, HVI_COLORS[2]],
      [50, HVI_COLORS[3]],
      [65, HVI_COLORS[4]],
      [80, HVI_COLORS[5]],
    ];
    for (const [score, expected] of cases) {
      expect(hviColor(score)).toBe(expected);
    }
  });

  it("returns the highest bin color for 100", () => {
    expect(hviColor(100)).toBe(HVI_COLORS[HVI_COLORS.length - 1]);
  });
});
