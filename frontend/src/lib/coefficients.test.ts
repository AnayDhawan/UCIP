/**
 * Issue #37.
 *
 * These are the highest-stakes pure functions in the frontend. They are not
 * decorative: each constant is transcribed from a specific cited paper, and a
 * slip here does not break the UI, it silently misrepresents the published
 * science the whole project stands on. So the expected values below are derived
 * from the citations themselves (see docs/references.md and the docstrings in
 * coefficients.ts), not from whatever the implementation happens to return.
 *
 * Papers under test:
 *   Ziter et al. 2019, PNAS 116(15):7575-7580        canopy cooling
 *   Santamouris 2014, Solar Energy 103:682-703       cool roofs / albedo
 *   Bowler et al. 2010, Landsc. Urban Plan. 97:147   park cool island
 */

import { describe, it, expect } from "vitest";
import {
  canopyCoolingC,
  coolRoofCoolingC,
  pocketParkCoolingC,
  simulate,
  CANOPY_THRESHOLD_PCT,
} from "./coefficients";

describe("canopyCoolingC (Ziter 2019)", () => {
  it("returns zero below the 40% canopy threshold", () => {
    // The paper's central nonlinear finding: below ~40% canopy within a 60-90m
    // radius there is no meaningful daytime air-temperature effect. Returning a
    // small linear value here would smooth over the exact result that makes the
    // citation worth having.
    expect(canopyCoolingC(0)).toBe(0);
    expect(canopyCoolingC(10)).toBe(0);
    expect(canopyCoolingC(39.9)).toBe(0);
  });

  it("returns zero exactly at the threshold", () => {
    expect(canopyCoolingC(CANOPY_THRESHOLD_PCT)).toBe(0);
    expect(CANOPY_THRESHOLD_PCT).toBe(40);
  });

  it("delivers the paper's full 1C at 80% canopy", () => {
    // Ziter: raising cover from 40% to 80% yields roughly 1C of daytime cooling.
    expect(canopyCoolingC(80)).toBeCloseTo(1.0, 10);
  });

  it("interpolates linearly between the threshold and the ceiling", () => {
    expect(canopyCoolingC(60)).toBeCloseTo(0.5, 10);
    expect(canopyCoolingC(50)).toBeCloseTo(0.25, 10);
    expect(canopyCoolingC(70)).toBeCloseTo(0.75, 10);
  });

  it("caps at the 80% value rather than extrapolating past the paper's data", () => {
    // Above 80% Ziter has no observations, so the honest answer is the ceiling,
    // not a larger number invented by the formula.
    expect(canopyCoolingC(90)).toBeCloseTo(1.0, 10);
    expect(canopyCoolingC(100)).toBeCloseTo(1.0, 10);
  });

  it("clamps out-of-range input instead of returning nonsense", () => {
    expect(canopyCoolingC(-20)).toBe(0);
    expect(canopyCoolingC(1000)).toBeCloseTo(1.0, 10);
  });

  it("never returns a negative cooling value", () => {
    for (let pct = -10; pct <= 110; pct += 5) {
      expect(canopyCoolingC(pct)).toBeGreaterThanOrEqual(0);
    }
  });
});

describe("coolRoofCoolingC (Santamouris 2014)", () => {
  it("returns zero for no albedo change", () => {
    const r = coolRoofCoolingC(0);
    expect(r.headlineC).toBe(0);
    expect(r.rangeLowC).toBe(0);
    expect(r.rangeHighC).toBe(0);
  });

  it("matches the paper's per-0.1-albedo figures at +0.1", () => {
    // Santamouris' city-scale review: peak ambient temperature falls roughly
    // 0.57-2.3K per +0.1 albedo. The headline uses the conservative 0.6K end,
    // per this project's own citation table.
    const r = coolRoofCoolingC(0.1);
    expect(r.headlineC).toBeCloseTo(0.6, 10);
    expect(r.rangeLowC).toBeCloseTo(0.57, 10);
    expect(r.rangeHighC).toBeCloseTo(2.3, 10);
  });

  it("scales linearly with albedo increase", () => {
    const r = coolRoofCoolingC(0.3);
    expect(r.headlineC).toBeCloseTo(1.8, 10);
    expect(r.rangeLowC).toBeCloseTo(1.71, 10);
    expect(r.rangeHighC).toBeCloseTo(6.9, 10);
  });

  it("keeps the headline inside the published uncertainty band", () => {
    // If someone edits the headline constant out of the cited range, the number
    // shown to users stops being defensible. Check across the whole domain.
    for (let d = 0; d <= 1.0001; d += 0.05) {
      const r = coolRoofCoolingC(d);
      expect(r.headlineC).toBeGreaterThanOrEqual(r.rangeLowC - 1e-9);
      expect(r.headlineC).toBeLessThanOrEqual(r.rangeHighC + 1e-9);
    }
  });

  it("clamps albedo increase to the physical 0-1 range", () => {
    expect(coolRoofCoolingC(-0.5).headlineC).toBe(0);
    expect(coolRoofCoolingC(5).headlineC).toBeCloseTo(coolRoofCoolingC(1).headlineC, 10);
  });
});

describe("pocketParkCoolingC (Bowler 2010)", () => {
  it("returns zero for no park area", () => {
    expect(pocketParkCoolingC(0)).toBe(0);
  });

  it("returns the meta-analysis ceiling of 0.94C at full coverage", () => {
    expect(pocketParkCoolingC(100)).toBeCloseTo(0.94, 10);
  });

  it("scales linearly with the converted fraction", () => {
    // The linear scaling is this project's own stated simplifying assumption,
    // not something Bowler models. Locking it here means a future change to that
    // assumption has to be deliberate.
    expect(pocketParkCoolingC(50)).toBeCloseTo(0.47, 10);
    expect(pocketParkCoolingC(25)).toBeCloseTo(0.235, 10);
  });

  it("clamps out-of-range input", () => {
    expect(pocketParkCoolingC(-10)).toBe(0);
    expect(pocketParkCoolingC(250)).toBeCloseTo(0.94, 10);
  });
});

describe("simulate", () => {
  it("sums the three terms as independent contributions", () => {
    const r = simulate(80, 0.1, 100);
    expect(r.canopyC).toBeCloseTo(1.0, 10);
    expect(r.coolRoof.headlineC).toBeCloseTo(0.6, 10);
    expect(r.parkC).toBeCloseTo(0.94, 10);
    expect(r.totalHeadlineC).toBeCloseTo(1.0 + 0.6 + 0.94, 10);
  });

  it("defaults park area to zero", () => {
    const r = simulate(80, 0.1);
    expect(r.parkC).toBe(0);
    expect(r.totalHeadlineC).toBeCloseTo(1.6, 10);
  });

  it("returns an all-zero result for a do-nothing scenario", () => {
    const r = simulate(0, 0, 0);
    expect(r.totalHeadlineC).toBe(0);
  });

  it("stays below the sum of the three published ceilings", () => {
    // A sanity bound on the whole estimator: no combination of sliders should
    // ever claim more cooling than the three papers permit added together.
    const maxPossible = 1.0 + 0.6 + 0.94;
    for (const canopy of [0, 40, 60, 100]) {
      for (const albedo of [0, 0.05, 0.1]) {
        for (const park of [0, 50, 100]) {
          expect(simulate(canopy, albedo, park).totalHeadlineC).toBeLessThanOrEqual(
            maxPossible + 1e-9
          );
        }
      }
    }
  });
});
