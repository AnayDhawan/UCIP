/**
 * Tests for the ward trend helpers (issue #89).
 *
 * The property that matters most is the one a chart makes it easy to break: a
 * slope that is not statistically significant must not be described as a
 * direction. On the current record no ward has a significant trend, so getting
 * this wrong would put a confident "warming" on all 24 of them.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describeSlope, seriesFor, sparklinePath, type TimeSeries, type WardTrend } from "./wardTrend";

const ward = (overrides: Partial<WardTrend> = {}): WardTrend => ({
  ward_id: "A",
  n_years: 3,
  trend: {
    lst_c_per_decade: 0.5,
    lst_stderr_c_per_decade: 0.2,
    lst_p_value: 0.01,
    lst_r_squared: 0.8,
    lst_significant: true,
    ndvi_per_decade: -0.01,
    ndvi_p_value: 0.02,
    ndvi_significant: true,
    classification: "warming",
  },
  series: [
    { year: 2020, LST_C: 30, NDVI: 0.2 },
    { year: 2021, LST_C: 32, NDVI: 0.25 },
    { year: 2022, LST_C: 31, NDVI: 0.22 },
  ],
  ...overrides,
});

describe("seriesFor", () => {
  it("extracts one measure with its years", () => {
    expect(seriesFor(ward(), "LST_C")).toEqual([
      { year: 2020, value: 30 },
      { year: 2021, value: 32 },
      { year: 2022, value: 31 },
    ]);
  });

  it("drops years the pipeline could not fit rather than plotting them as zero", () => {
    const withGap = ward({
      series: [
        { year: 2020, LST_C: 30, NDVI: null },
        { year: 2021, LST_C: null, NDVI: 0.25 },
      ],
    });
    expect(seriesFor(withGap, "LST_C")).toEqual([{ year: 2020, value: 30 }]);
    expect(seriesFor(withGap, "NDVI")).toEqual([{ year: 2021, value: 0.25 }]);
  });
});

describe("describeSlope", () => {
  it("names a direction only when the slope is significant", () => {
    expect(describeSlope(0.5, true, "C", "warming", "cooling")).toContain("warming");
    expect(describeSlope(-0.5, true, "C", "warming", "cooling")).toContain("cooling");
  });

  it("refuses to name a direction when the slope is not significant", () => {
    // The whole point. All 24 wards are in this branch on the current record.
    const text = describeSlope(0.5, false, "C", "warming", "cooling");
    expect(text).toContain("no detected trend");
    expect(text).not.toContain("warming");
  });

  it("still shows the estimate when it is not significant", () => {
    // Hiding it would overstate the certainty in the other direction.
    expect(describeSlope(-0.43, false, "C", "warming", "cooling")).toContain("0.43");
  });
});

describe("sparklinePath", () => {
  it("spans the full width and inverts y, so up on screen is a higher value", () => {
    const path = sparklinePath(
      [
        { year: 2020, value: 0 },
        { year: 2021, value: 10 },
      ],
      100,
      20
    );
    expect(path).toBe("M0.00,20.00L100.00,0.00");
  });

  it("draws a flat series down the middle rather than dividing by zero", () => {
    const path = sparklinePath(
      [
        { year: 2020, value: 5 },
        { year: 2021, value: 5 },
      ],
      100,
      20
    );
    expect(path).toBe("M0.00,10.00L100.00,10.00");
    expect(path).not.toContain("NaN");
  });

  it("returns nothing for an empty series", () => {
    expect(sparklinePath([], 100, 20)).toBe("");
  });

  it("handles a single point without producing NaN", () => {
    expect(sparklinePath([{ year: 2020, value: 5 }], 100, 20)).toBe("M0,10L100,10");
  });
});

describe("the published time series", () => {
  const path = join(process.cwd(), "public", "ward_timeseries.json");
  let data: TimeSeries | null = null;
  try {
    data = JSON.parse(readFileSync(path, "utf8")) as TimeSeries;
  } catch {
    data = null;
  }

  it("covers all 24 wards", () => {
    if (!data) return;
    expect(data.wards).toHaveLength(24);
  });

  it("every ward renders a path without NaN", () => {
    if (!data) return;
    for (const w of data.wards) {
      for (const measure of ["LST_C", "NDVI"] as const) {
        const points = seriesFor(w, measure);
        if (points.length < 2) continue;
        expect(sparklinePath(points, 96, 24), `${w.ward_id} ${measure}`).not.toContain("NaN");
      }
    }
  });

  it("no ward is currently described with a direction", () => {
    if (!data) return;
    // Documents the state of the record rather than asserting it forever: if a
    // future refresh finds a significant trend this fails, and the failure is
    // the notification that the claim on screen has changed.
    expect(data.summary.n_wards_significant).toBe(0);
    for (const w of data.wards) {
      const text = describeSlope(w.trend.lst_c_per_decade, w.trend.lst_significant, "C", "warming", "cooling");
      expect(text, w.ward_id).toContain("no detected trend");
    }
  });
});
