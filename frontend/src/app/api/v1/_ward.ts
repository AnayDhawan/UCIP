/**
 * The ward object, defined once.
 *
 * /wards, /wards/{id} and /lookup all return a `Ward`, and the OpenAPI spec has
 * one `Ward` schema, so the three routes have to produce the same keys. They
 * used to build the object separately and drifted (issue #204): only /wards
 * carried the dominance fields, and /lookup dropped `contrib` on the snapshot
 * path. Both halves of the contract live here so a change cannot reach one
 * route and miss the others.
 */

import type { WardProps } from "@/lib/wardTypes";

export type WardRow = {
  ward_id: string;
  hvi: number | null;
  rank: number | null;
  n_cells: number | null;
  contrib: Record<string, number> | null;
  // Which indicator drives this ward's score (issue #97). Computed in the
  // pipeline so the GeoJSON, the CSV export and the database agree; see
  // DOMINANCE_THRESHOLD in pipeline/_hvi.py for what "dominated" means.
  dominant_factor: string | null;
  dominant_share: number | null;
  single_factor_dominated: boolean | null;
};

/**
 * Every field the API promises for a ward, in one string.
 *
 * This is the database half of the contract that `fromSnapshot` below is the
 * snapshot half of. Both must produce the same keys: a consumer cannot tell
 * which source answered, and should not have to.
 */
export const WARD_COLUMNS =
  "ward_id,hvi,rank,n_cells,contrib,dominant_factor,dominant_share,single_factor_dominated";

/** Snapshot properties use SCREAMING keys and flat contrib_* fields; the API does not. */
export function fromSnapshot(p: WardProps): WardRow {
  const contrib: Record<string, number> = {};
  for (const [key, value] of Object.entries(p)) {
    if (key.startsWith("contrib_") && typeof value === "number") {
      contrib[key.slice("contrib_".length)] = value;
    }
  }
  return {
    ward_id: p.ward_id,
    hvi: p.HVI,
    rank: p.rank,
    n_cells: p.n_cells,
    contrib: Object.keys(contrib).length ? contrib : null,
    dominant_factor: p.dominant_factor ?? null,
    dominant_share: p.dominant_share ?? null,
    single_factor_dominated: p.single_factor_dominated ?? null,
  };
}
