/**
 * Issue #36. Extends the original bin-boundary suite to cover every edge of the
 * ramp exhaustively.
 *
 * hviColor looks trivial, but the ramp is semantic rather than decorative:
 * DESIGN.md locks these six hexes, and the map, the ward list, the landing page
 * and the 3D hero all colour from this one function. An off-by-one on a bin edge
 * does not look like a bug, it looks like a ward changed severity.
 */

import { describe, it, expect } from "vitest";
import { hviColor, HVI_COLORS, HVI_BIN_MAX, HVI_NO_DATA_COLOR } from "./hvi";

describe("hviColor no-data handling", () => {
  it("returns the no-data gray for null", () => {
    expect(hviColor(null)).toBe(HVI_NO_DATA_COLOR);
  });

  it("returns the no-data gray for undefined", () => {
    expect(hviColor(undefined)).toBe(HVI_NO_DATA_COLOR);
  });

  it("returns the no-data gray for NaN", () => {
    expect(hviColor(NaN)).toBe(HVI_NO_DATA_COLOR);
  });

  it("does not treat 0 as missing", () => {
    // 0 is a real score, and a truthiness check instead of an explicit null
    // check would grey out the least vulnerable wards on the map.
    expect(hviColor(0)).toBe(HVI_COLORS[0]);
  });
});

describe("hviColor bin boundaries", () => {
  it("maps every bin edge to the bin above it", () => {
    // Bins are half-open [lower, upper), so the boundary value itself belongs to
    // the NEXT bin. This is the exact off-by-one worth locking down.
    expect(hviColor(19.999)).toBe(HVI_COLORS[0]);
    expect(hviColor(20)).toBe(HVI_COLORS[1]);
    expect(hviColor(34.999)).toBe(HVI_COLORS[1]);
    expect(hviColor(35)).toBe(HVI_COLORS[2]);
    expect(hviColor(49.999)).toBe(HVI_COLORS[2]);
    expect(hviColor(50)).toBe(HVI_COLORS[3]);
    expect(hviColor(64.999)).toBe(HVI_COLORS[3]);
    expect(hviColor(65)).toBe(HVI_COLORS[4]);
    expect(hviColor(79.999)).toBe(HVI_COLORS[4]);
    expect(hviColor(80)).toBe(HVI_COLORS[5]);
  });

  it("maps a mid-bin value in every bin", () => {
    expect(hviColor(10)).toBe(HVI_COLORS[0]);
    expect(hviColor(27)).toBe(HVI_COLORS[1]);
    expect(hviColor(42)).toBe(HVI_COLORS[2]);
    expect(hviColor(57)).toBe(HVI_COLORS[3]);
    expect(hviColor(72)).toBe(HVI_COLORS[4]);
    expect(hviColor(90)).toBe(HVI_COLORS[5]);
  });

  it("holds the top colour to the end of the scale and beyond", () => {
    expect(hviColor(100)).toBe(HVI_COLORS[5]);
    expect(hviColor(1000)).toBe(HVI_COLORS[5]);
    expect(hviColor(Infinity)).toBe(HVI_COLORS[5]);
  });

  it("puts negative scores in the lowest bin rather than off the ramp", () => {
    expect(hviColor(-5)).toBe(HVI_COLORS[0]);
    expect(hviColor(-Infinity)).toBe(HVI_COLORS[0]);
  });

  it("returns a colour for every value across the whole 0-100 scale", () => {
    for (let v = 0; v <= 100; v += 0.5) {
      expect(HVI_COLORS as readonly string[]).toContain(hviColor(v));
    }
  });

  it("increases monotonically through the ramp as the score rises", () => {
    // The ramp must never go backwards: a hotter ward can never render cooler.
    let lastIndex = 0;
    for (let v = 0; v <= 100; v += 0.25) {
      const index = (HVI_COLORS as readonly string[]).indexOf(hviColor(v));
      expect(index).toBeGreaterThanOrEqual(lastIndex);
      lastIndex = index;
    }
  });
});

describe("the ramp definition", () => {
  it("keeps HVI_BIN_MAX aligned 1:1 with HVI_COLORS", () => {
    // The loop in hviColor indexes both arrays together; a length mismatch would
    // silently drop the top bin or read undefined.
    expect(HVI_BIN_MAX).toHaveLength(HVI_COLORS.length);
  });

  it("has strictly ascending bin edges ending at Infinity", () => {
    for (let i = 1; i < HVI_BIN_MAX.length; i++) {
      expect(HVI_BIN_MAX[i]).toBeGreaterThan(HVI_BIN_MAX[i - 1]);
    }
    expect(HVI_BIN_MAX[HVI_BIN_MAX.length - 1]).toBe(Infinity);
  });

  it("uses six distinct, valid hex colours", () => {
    expect(new Set(HVI_COLORS).size).toBe(HVI_COLORS.length);
    for (const hex of HVI_COLORS) {
      expect(hex).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });

  it("keeps the no-data gray out of the data ramp", () => {
    // If the no-data colour ever collided with a real bin, a scored ward and an
    // unscored one would be indistinguishable on the map.
    expect(HVI_COLORS as readonly string[]).not.toContain(HVI_NO_DATA_COLOR);
  });
});
