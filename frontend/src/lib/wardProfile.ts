/**
 * Ward profiles: the shape of `public/ward_profiles.json` (written by
 * pipeline/10_ward_profile.py) plus the plain-language rendering of it.
 *
 * Every sentence and every formatted figure here traces back to a field in that
 * file. Nothing is invented, nothing is rounded into a claim the data does not
 * support, and proxies are named as proxies: NDVI is a vegetation index, not a
 * canopy percentage, and the elderly and slum layers are modelled surfaces
 * rather than ward-level census (docs/methodology.md, section 10).
 *
 * Kept as pure functions so the copy is deterministic and reviewable without
 * rendering anything.
 */

import en from "./i18n/dictionaries/en";
import { format, type Dictionary } from "./i18n";
import { FACTOR_LABELS, type IndicatorKey } from "./wardTypes";

export type CityProfile = {
  hvi_mean: number;
  LST_C: number;
  NDVI: number;
  pop_density_km2: number;
  elderly_pct: number;
  child_pct: number;
  slum_pct: number;
  hospital_dist_m: number;
  impervious_pct: number;
};

export type NeighbourRef = { ward_id: string; hvi: number };

export type WardProfile = {
  ward_id: string;
  ward_gid: number;
  hvi: number | null;
  rank: number | null;
  n_cells: number | null;
  percentile: number | null;
  LST_C: number;
  LST_C_delta_city: number;
  NDVI: number;
  NDVI_delta_city: number;
  pop_density_km2: number;
  pop_density_km2_delta_city: number;
  elderly_pct: number;
  elderly_pct_delta_city: number;
  child_pct: number;
  child_pct_delta_city: number;
  slum_pct: number;
  slum_pct_delta_city: number;
  hospital_dist_m: number;
  hospital_dist_m_delta_city: number;
  impervious_pct: number;
  impervious_pct_delta_city: number;
  top_driver?: IndicatorKey;
  top_driver_contrib?: number;
  neighbours: string[];
  coolest_neighbour?: NeighbourRef;
  hottest_neighbour?: NeighbourRef;
};

export type WardProfileData = {
  generated_from: string;
  n_cells: number;
  n_wards: number;
  indicators: IndicatorKey[];
  units: Record<string, string>;
  city: CityProfile;
  wards: WardProfile[];
};

export const WARD_PROFILES_URL = "/ward_profiles.json";

/** Below this the ward is not meaningfully warmer or cooler than the city. */
const TEMP_PARITY_C = 0.15;

export function fmtTemp(c: number): string {
  return `${c.toFixed(1)} C`;
}

export function fmtNdvi(v: number): string {
  return v.toFixed(2);
}

export function fmtPct(v: number): string {
  return `${Math.round(v)}%`;
}

/** People per square kilometre, rounded to the nearest hundred. Precision past
 *  that would imply the WorldPop surface is sharper than it is. Indian digit
 *  grouping, since this is a Mumbai civic tool. */
export function fmtDensity(v: number): string {
  return (Math.round(v / 100) * 100).toLocaleString("en-IN");
}

export function fmtDistance(m: number): string {
  if (m >= 1000) return `${(m / 1000).toFixed(1)} km`;
  return `${Math.round(m / 10) * 10} m`;
}

/** "1st", "2nd", "3rd", "4th" ... */
export function ordinal(n: number): string {
  const rem100 = n % 100;
  if (rem100 >= 11 && rem100 <= 13) return `${n}th`;
  switch (n % 10) {
    case 1:
      return `${n}st`;
    case 2:
      return `${n}nd`;
    case 3:
      return `${n}rd`;
    default:
      return `${n}th`;
  }
}

export function factorLabel(key: IndicatorKey): string {
  return FACTOR_LABELS[key];
}

/**
 * Two or three sentences describing the ward from its measured indicators.
 * Reads as prose, but every number is a field lookup.
 */
export function describeWard(
  ward: WardProfile,
  city: CityProfile,
  t: Dictionary = en
): string[] {
  const s = t.ward.summary;
  const sentences: string[] = [];

  const delta = ward.LST_C_delta_city;
  const cells = ward.n_cells ?? 0;
  const cellPhrase = cells === 1 ? s.oneCell : format(s.manyCells, { n: cells });
  if (Math.abs(delta) < TEMP_PARITY_C) {
    sentences.push(
      format(s.parity, { ward: ward.ward_id, cells: cellPhrase, temp: fmtTemp(ward.LST_C) })
    );
  } else {
    sentences.push(
      format(s.offset, {
        ward: ward.ward_id,
        delta: fmtTemp(Math.abs(delta)),
        direction: delta > 0 ? s.hotter : s.cooler,
        cells: cellPhrase,
        temp: fmtTemp(ward.LST_C),
      })
    );
  }

  sentences.push(
    format(s.green, {
      ndvi: fmtNdvi(ward.NDVI),
      cityNdvi: fmtNdvi(city.NDVI),
      built: fmtPct(ward.impervious_pct),
    })
  );

  sentences.push(
    format(s.people, {
      density: fmtDensity(ward.pop_density_km2),
      distance: fmtDistance(ward.hospital_dist_m),
    })
  );

  return sentences;
}

/** One line on which factor pushes this ward's score up hardest. */
export function describeTopDriver(ward: WardProfile, t: Dictionary = en): string | null {
  if (!ward.top_driver) return null;
  // Lower-cased for English, which puts the factor mid-sentence. Devanagari has
  // no case, so toLowerCase() leaves Marathi and Hindi untouched.
  return format(t.ward.biggestDriver, {
    factor: t.ward.factors[ward.top_driver].toLowerCase(),
  });
}
