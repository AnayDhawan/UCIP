/**
 * Issue #39.
 *
 * wardProfile.ts turns measured indicators into the prose a resident actually
 * reads in the ward dialog. Its own docstring is explicit that nothing may be
 * invented and nothing rounded into a claim the data does not support, so these
 * tests check the copy against the fixture data, not merely that the functions
 * return a string.
 */

import { describe, it, expect } from "vitest";
import {
  fmtTemp,
  fmtNdvi,
  fmtPct,
  fmtDensity,
  fmtDistance,
  ordinal,
  factorLabel,
  describeWard,
  describeTopDriver,
  type WardProfile,
  type CityProfile,
} from "./wardProfile";

const city: CityProfile = {
  hvi_mean: 50,
  LST_C: 32.4,
  NDVI: 0.37,
  pop_density_km2: 27500,
  elderly_pct: 9.1,
  slum_pct: 32,
  hospital_dist_m: 1400,
  impervious_pct: 61,
};

function ward(overrides: Partial<WardProfile> = {}): WardProfile {
  return {
    ward_id: "F/N",
    ward_gid: 7,
    hvi: 71.2,
    rank: 3,
    n_cells: 22,
    percentile: 87,
    LST_C: 34.1,
    LST_C_delta_city: 1.7,
    NDVI: 0.28,
    NDVI_delta_city: -0.09,
    pop_density_km2: 41250,
    pop_density_km2_delta_city: 13750,
    elderly_pct: 10.4,
    elderly_pct_delta_city: 1.3,
    slum_pct: 44,
    slum_pct_delta_city: 12,
    hospital_dist_m: 820,
    hospital_dist_m_delta_city: -580,
    impervious_pct: 73,
    impervious_pct_delta_city: 12,
    top_driver: "LST_C",
    top_driver_contrib: 0.31,
    neighbours: ["G/N", "L"],
    ...overrides,
  };
}

describe("formatters", () => {
  it("fmtTemp keeps one decimal and labels the unit", () => {
    expect(fmtTemp(34.14)).toBe("34.1 C");
    expect(fmtTemp(34)).toBe("34.0 C");
    expect(fmtTemp(0)).toBe("0.0 C");
    expect(fmtTemp(-1.25)).toBe("-1.3 C");
  });

  it("fmtNdvi keeps two decimals, matching the index's real precision", () => {
    expect(fmtNdvi(0.283)).toBe("0.28");
    expect(fmtNdvi(0)).toBe("0.00");
    // NDVI is defined on [-1, 1]; negative values are water, not an error.
    expect(fmtNdvi(-0.14)).toBe("-0.14");
  });

  it("fmtPct rounds to a whole percentage", () => {
    expect(fmtPct(73.4)).toBe("73%");
    expect(fmtPct(73.5)).toBe("74%");
    expect(fmtPct(0)).toBe("0%");
    expect(fmtPct(100)).toBe("100%");
  });

  it("fmtDensity rounds to the nearest hundred with Indian digit grouping", () => {
    // Precision past a hundred would imply the WorldPop surface is sharper than
    // it is; the grouping is en-IN because this is a Mumbai civic tool.
    expect(fmtDensity(41249)).toBe("41,200");
    expect(fmtDensity(41250)).toBe("41,300");
    expect(fmtDensity(0)).toBe("0");
    expect(fmtDensity(1250000)).toBe("12,50,000");
  });

  it("fmtDistance switches to kilometres at 1000m", () => {
    expect(fmtDistance(824)).toBe("820 m");
    expect(fmtDistance(1000)).toBe("1.0 km");
    expect(fmtDistance(1500)).toBe("1.5 km");
    expect(fmtDistance(2340)).toBe("2.3 km");
    expect(fmtDistance(0)).toBe("0 m");
  });

  it("fmtDistance rounds sub-kilometre distances to the nearest 10m", () => {
    expect(fmtDistance(824)).toBe("820 m");
    expect(fmtDistance(825)).toBe("830 m");
    // 999 rounds up to 1000 and still prints in metres, because the km switch
    // tests the raw input rather than the rounded output.
    expect(fmtDistance(999)).toBe("1000 m");
  });
});

describe("ordinal", () => {
  it("handles the common suffixes", () => {
    expect(ordinal(1)).toBe("1st");
    expect(ordinal(2)).toBe("2nd");
    expect(ordinal(3)).toBe("3rd");
    expect(ordinal(4)).toBe("4th");
    expect(ordinal(24)).toBe("24th");
  });

  it("handles the 11/12/13 exception", () => {
    // The classic ordinal trap: 11-13 take "th" despite ending in 1, 2, 3.
    expect(ordinal(11)).toBe("11th");
    expect(ordinal(12)).toBe("12th");
    expect(ordinal(13)).toBe("13th");
  });

  it("resumes the normal pattern after the exception", () => {
    expect(ordinal(21)).toBe("21st");
    expect(ordinal(22)).toBe("22nd");
    expect(ordinal(23)).toBe("23rd");
  });

  it("handles the exception again in the hundreds", () => {
    expect(ordinal(111)).toBe("111th");
    expect(ordinal(112)).toBe("112th");
    expect(ordinal(113)).toBe("113th");
    expect(ordinal(101)).toBe("101st");
  });
});

describe("factorLabel", () => {
  it("returns a human label for each indicator key used in the fixture", () => {
    expect(factorLabel("LST_C")).toBeTruthy();
    expect(factorLabel("NDVI")).toBeTruthy();
  });
});

describe("describeWard", () => {
  it("states the measured temperature and the delta, both traceable to fields", () => {
    const [first] = describeWard(ward(), city);
    expect(first).toContain("F/N");
    expect(first).toContain("1.7 C");
    expect(first).toContain("hotter");
    expect(first).toContain("34.1 C");
  });

  it("says cooler when the ward is below the city average", () => {
    const [first] = describeWard(ward({ LST_C_delta_city: -1.2, LST_C: 31.2 }), city);
    expect(first).toContain("cooler");
    // The magnitude is stated unsigned; the direction is carried by the word.
    expect(first).toContain("1.2 C");
    expect(first).not.toContain("-1.2");
  });

  it("claims parity rather than a direction inside the noise threshold", () => {
    // Below 0.15C the difference is not meaningful, so the copy must not assert
    // that the ward is hotter or cooler at all.
    const [first] = describeWard(ward({ LST_C_delta_city: 0.05 }), city);
    expect(first).toContain("about as warm as");
    expect(first).not.toContain("hotter");
    expect(first).not.toContain("cooler");
  });

  it("pluralises the grid-cell count correctly", () => {
    expect(describeWard(ward({ n_cells: 1 }), city)[0]).toContain("its single grid cell");
    expect(describeWard(ward({ n_cells: 22 }), city)[0]).toContain("its 22 grid cells");
  });

  it("quotes both the ward and city NDVI so the comparison is checkable", () => {
    const sentences = describeWard(ward(), city);
    expect(sentences[1]).toContain("0.28");
    expect(sentences[1]).toContain("0.37");
    expect(sentences[1]).toContain("73%");
  });

  it("reports density and hospital distance from the fields, formatted", () => {
    const sentences = describeWard(ward(), city);
    expect(sentences[2]).toContain("41,300");
    expect(sentences[2]).toContain("820 m");
  });

  it("invents no numbers beyond those present in the profile", () => {
    // Every numeric token in the prose must be derivable from the fixture. This
    // is the "no invented claims" rule from the module docstring, enforced.
    const w = ward();
    const allowed = new Set(
      [
        fmtTemp(Math.abs(w.LST_C_delta_city)),
        fmtTemp(w.LST_C),
        fmtNdvi(w.NDVI),
        fmtNdvi(city.NDVI),
        fmtPct(w.impervious_pct),
        fmtDensity(w.pop_density_km2),
        fmtDistance(w.hospital_dist_m),
        String(w.n_cells),
      ].flatMap((s) => s.match(/[\d.,]+/g) ?? [])
    );

    for (const sentence of describeWard(w, city)) {
      for (const token of sentence.match(/[\d][\d.,]*/g) ?? []) {
        expect(allowed.has(token), `unexplained number "${token}" in: ${sentence}`).toBe(true);
      }
    }
  });

  it("returns three sentences", () => {
    expect(describeWard(ward(), city)).toHaveLength(3);
  });
});

describe("describeTopDriver", () => {
  it("names the driving factor in lowercase prose", () => {
    const line = describeTopDriver(ward())!;
    expect(line).toContain("Biggest driver:");
    expect(line).toBe(`Biggest driver: ${factorLabel("LST_C").toLowerCase()}.`);
  });

  it("returns null when no driver was computed", () => {
    // A ward with no top_driver must render nothing rather than a sentence with
    // a blank or "undefined" in it.
    expect(describeTopDriver(ward({ top_driver: undefined }))).toBeNull();
  });
});
