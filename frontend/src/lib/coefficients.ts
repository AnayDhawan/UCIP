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

/**
 * Pocket-park / green-open-space cooling, from Bowler et al. 2010 (Landscape and Urban
 * Planning 97:147-155, doi:10.1016/j.landurbplan.2010.05.006), a systematic review/
 * meta-analysis of park-vs-surroundings temperature studies: parks are, on average,
 * ~0.94C cooler in the day than their built surroundings (the "park cool island" effect).
 *
 * That figure is a per-park comparison, not a function of ward-wide coverage — the
 * paper does not model "what if X% of a ward were parkland." Scaling the 0.94C ceiling
 * linearly by the fraction of ward area converted to park-like green space is this
 * project's own simplifying assumption, stated here rather than hidden: at 100% coverage
 * every point in the ward is inside the park's cooled zone (the full effect); at partial
 * coverage only that fraction of the ward benefits, averaged across the whole area.
 */
export function pocketParkCoolingC(parkAreaPct: number): number {
  const pct = Math.min(Math.max(parkAreaPct, 0), 100);
  const MAX_COOLING_C = 0.94;
  return (pct / 100) * MAX_COOLING_C;
}

export type SimulationResult = {
  canopyC: number;
  coolRoof: CoolRoofEstimate;
  parkC: number;
  totalHeadlineC: number;
};

/**
 * Sums the three interventions as independent illustrative terms. This is explicitly
 * not a coupled physical simulation — canopy, cool-roof, and pocket-park effects are
 * not modeled as interacting with each other (e.g. no double-counting check between
 * canopy cover and park area, even though parks often contain trees).
 */
export function simulate(
  canopyPct: number,
  albedoIncrease: number,
  parkAreaPct: number = 0,
): SimulationResult {
  const canopyC = canopyCoolingC(canopyPct);
  const coolRoof = coolRoofCoolingC(albedoIncrease);
  const parkC = pocketParkCoolingC(parkAreaPct);
  return {
    canopyC,
    coolRoof,
    parkC,
    totalHeadlineC: canopyC + coolRoof.headlineC + parkC,
  };
}

export const CANOPY_THRESHOLD_PCT = 40;
