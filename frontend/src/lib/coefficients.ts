/**
 * Cited coefficient estimator behind `/simulate`. This is deliberately NOT a trained
 * model: every constant below traces to a specific cited paper (see `citations.ts`),
 * and the functions never extrapolate past what that paper actually measured. All
 * numbers are illustrative first-order estimates transferred from other cities, not
 * Mumbai-calibrated — that limitation is surfaced in `/simulate`'s UI, not just here.
 */

/**
 * Tree-canopy cooling, from Ziter et al. 2019 (PNAS 116(15):7575-7580,
 * doi:10.1073/pnas.1817561116). Their finding: canopy cover below ~40% within a
 * 60-90m radius produces negligible daytime air-temperature change; raising cover
 * from 40% to 80% delivers roughly 1C of daytime cooling. Below the 40% threshold
 * this returns 0 rather than a small linear value, matching the paper's own
 * nonlinear finding instead of smoothing over it. Above 80% the paper has no data,
 * so the estimate is capped at the 80% value rather than extrapolated.
 */
export function canopyCoolingC(canopyPct: number): number {
  const pct = Math.min(Math.max(canopyPct, 0), 100);
  const THRESHOLD = 40;
  const CEILING = 80;
  const MAX_COOLING_C = 1.0;
  if (pct <= THRESHOLD) return 0;
  const capped = Math.min(pct, CEILING);
  return ((capped - THRESHOLD) / (CEILING - THRESHOLD)) * MAX_COOLING_C;
}

export type CoolRoofEstimate = {
  headlineC: number;
  rangeLowC: number;
  rangeHighC: number;
};

/**
 * Cool-roof / high-albedo cooling. Quantitative range from Santamouris 2014
 * (Solar Energy 103:682-703, doi:10.1016/j.solener.2012.07.003): peak ambient
 * temperature falls roughly 0.57-2.3K per +0.1 increase in surface albedo across
 * the city-scale review's studies. The headline number uses the conservative end
 * (0.6K per +0.1) per the project's own citation table; the full range is exposed
 * as an uncertainty band rather than hidden.
 *
 * Li, Bou-Zeid & Oppenheimer 2014 (Environ. Res. Lett. 9(5):055002,
 * doi:10.1088/1748-9326/9/5/055002) is cited alongside as qualitative/structural
 * support only — their WRF+PUCM simulation shows surface and near-surface UHI
 * falling roughly linearly with cool-roof fraction, which supports treating this
 * relationship as linear, but the paper does not publish a portable K-per-albedo
 * slope, so no second numeric coefficient is derived from it here.
 */
export function coolRoofCoolingC(albedoIncrease: number): CoolRoofEstimate {
  const delta = Math.min(Math.max(albedoIncrease, 0), 1);
  const HEADLINE_PER_0_1 = 0.6;
  const LOW_PER_0_1 = 0.57;
  const HIGH_PER_0_1 = 2.3;
  const units = delta / 0.1;
  return {
    headlineC: units * HEADLINE_PER_0_1,
    rangeLowC: units * LOW_PER_0_1,
    rangeHighC: units * HIGH_PER_0_1,
  };
}

export type SimulationResult = {
  canopyC: number;
  coolRoof: CoolRoofEstimate;
  totalHeadlineC: number;
};

/**
 * Sums the two interventions as independent illustrative terms. This is explicitly
 * not a coupled physical simulation — canopy and cool-roof effects are not modeled
 * as interacting with each other.
 */
export function simulate(canopyPct: number, albedoIncrease: number): SimulationResult {
  const canopyC = canopyCoolingC(canopyPct);
  const coolRoof = coolRoofCoolingC(albedoIncrease);
  return {
    canopyC,
    coolRoof,
    totalHeadlineC: canopyC + coolRoof.headlineC,
  };
}

export const CANOPY_THRESHOLD_PCT = 40;
