/**
 * GET /api/v1/wards
 *
 * All 24 BMC wards with their heat vulnerability index, rank and per-factor
 * contributions, ranked most vulnerable first.
 *
 * Query params:
 *   limit     1-24, default 24
 *   geometry  "true" to include ward polygons (large; off by default)
 */

import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { WardProps } from "@/lib/wardTypes";
import {
  errorResponse,
  jsonResponse,
  optionsResponse,
  parseLimit,
  readSnapshot,
  rateLimited,
  supabase,
} from "../_lib";

export const revalidate = 3600;

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
const WARD_COLUMNS =
  "ward_id,hvi,rank,n_cells,contrib,dominant_factor,dominant_share,single_factor_dominated";

/** Snapshot properties use SCREAMING keys and flat contrib_* fields; the API does not. */
function fromSnapshot(p: WardProps): WardRow {
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

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const limited = await rateLimited(request);
  if (limited) return limited;

  const url = new URL(request.url);
  const limit = parseLimit(url.searchParams.get("limit"), 24, 24);
  const wantGeometry = url.searchParams.get("geometry") === "true";

  const db = supabase();
  if (db) {
    // The dominance columns are selected explicitly. They were added to the
    // table in 0007 and to the snapshot path above, but were missing from this
    // list, so a database-backed response silently dropped the #97 flag while
    // the snapshot response and the CSV export both carried it. Same endpoint,
    // two different shapes depending on which source answered.
    const columns = wantGeometry
      ? `${WARD_COLUMNS},geom_geojson`
      : WARD_COLUMNS;
    const { data, error } = await db
      .from("wards")
      .select(columns)
      .order("rank", { ascending: true })
      .limit(limit);

    if (!error && data) {
      return jsonResponse({ source: "database", count: data.length, wards: data });
    }
    // Fall through to the snapshot rather than surfacing a database outage as a
    // 500. The static files are the same data, one refresh behind at worst.
  }

  try {
    const geo = await readSnapshot<FeatureCollection<Geometry, WardProps>>("wards_hvi.geojson");
    const wards = [...geo.features]
      .sort((a, b) => (a.properties.rank ?? 99) - (b.properties.rank ?? 99))
      .slice(0, limit)
      .map((f: Feature<Geometry, WardProps>) => ({
        ...fromSnapshot(f.properties),
        ...(wantGeometry ? { geom_geojson: f.geometry } : {}),
      }));
    return jsonResponse({ source: "snapshot", count: wards.length, wards });
  } catch {
    return errorResponse(503, "Ward data is temporarily unavailable.");
  }
}
