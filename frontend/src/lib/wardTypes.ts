/**
 * Ward record shapes, in one place.
 *
 * Previously duplicated (and already drifting) between WardChoropleth.tsx and
 * WardPanel.tsx: one carried the contrib_* fields, the other did not, and their
 * two NbsRec types disagreed about `cell_count`. The ward dialog is the third
 * consumer, so they live here now.
 */

/** A feature property bag from `public/wards_hvi.geojson`, written by pipeline/05_hvi.py. */
export type WardProps = {
  ward_id: string;
  ward_gid: number;
  HVI: number | null;
  rank: number | null;
  n_cells: number | null;
  contrib_LST_C: number | null;
  contrib_NDVI: number | null;
  contrib_pop_density_km2: number | null;
  contrib_elderly_pct: number | null;
  contrib_slum_pct: number | null;
  contrib_hospital_dist_m: number | null;
  contrib_impervious_pct: number | null;
  [key: string]: unknown;
};

/** A row of `public/nbs_recommendations.json`, written by pipeline/06_nbs.py. */
export type NbsRec = {
  ward_id: string;
  intervention: string;
  rationale: string;
  citation: string;
  priority: number;
  cell_count: number;
};

/** A 1 km grid cell on the plantability layer (`public/cells_nbs.geojson`). */
export type CellNbsProps = {
  grid_id: number;
  ward_id: string;
  HVI: number | null;
  plantable: boolean | number | null;
  worldcover_class: number | null;
  [key: string]: unknown;
};

/** A 1 km grid cell on the green-cover-change layer (`public/cells_ndvi_change.geojson`). */
export type CellNdviProps = {
  grid_id: number;
  ward_id: string;
  NDVI: number | null;
  NDVI_prev: number | null;
  ndvi_delta: number | null;
  change_class: "gained" | "stable" | "lost" | "unknown" | null;
  [key: string]: unknown;
};

/** The seven HVI indicators, in the canonical order used by pipeline/05_hvi.py. */
export const INDICATOR_KEYS = [
  "LST_C",
  "NDVI",
  "pop_density_km2",
  "elderly_pct",
  "slum_pct",
  "hospital_dist_m",
  "impervious_pct",
] as const;

export type IndicatorKey = (typeof INDICATOR_KEYS)[number];

/** Plain-language labels for the seven factors, shared by the bars and the table. */
export const FACTOR_LABELS: Record<IndicatorKey, string> = {
  LST_C: "Land surface temp",
  NDVI: "Green cover (NDVI)",
  pop_density_km2: "Population density",
  elderly_pct: "Elderly %",
  slum_pct: "Slum index",
  hospital_dist_m: "Hospital distance",
  impervious_pct: "Impervious / built-up",
};

/** Contribution values (weight x z-score) mostly fall in [-0.3, 0.3]. */
export const CONTRIB_BAR_MAX = 0.3;
