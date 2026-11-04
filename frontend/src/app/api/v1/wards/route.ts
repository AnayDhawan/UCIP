/**
 * GET /api/v1/wards
 *
 * All 24 BMC wards with their heat vulnerability index, rank and per-factor
 * contributions, ranked most vulnerable first.
 *
 * Query params:
 *   limit     1-24, default 24
 *   geometry  "true" to include ward polygons (large; off by default)
 *
 * Each ward also carries rank_ci_low / rank_ci_high (and hvi_ci_low /
 * hvi_ci_high), the 95% bootstrap interval from hvi_uncertainty.json. They are
 * omitted when that file has no entry for the ward.
 */

import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { WardProps } from "@/lib/wardTypes";
import { WARD_COLUMNS, fromSnapshot, type WardRow } from "../_ward";

export type { WardRow } from "../_ward";
import {
  errorResponse,
  intervalFields,
  jsonResponse,
  logFallback,
  optionsResponse,
  parseLimit,
  readIntervals,
  readSnapshot,
  rateLimited,
  supabase,
} from "../_lib";

export const revalidate = 3600;

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const limited = await rateLimited(request);
  if (limited) return limited;

  const url = new URL(request.url);
  const limit = parseLimit(url.searchParams.get("limit"), 24, 24);
  if (limit === null) {
    return errorResponse(400, "'limit' must be a positive integer.", "Example: limit=10");
  }
  const wantGeometry = url.searchParams.get("geometry") === "true";

  const intervals = await readIntervals();

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
      const wards = (data as unknown as WardRow[]).map((w) => ({
        ...w,
        ...intervalFields(intervals, w.ward_id, w.rank),
      }));
      return jsonResponse({ source: "database", count: wards.length, wards });
    }
    logFallback("/wards", error);
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
        ...intervalFields(intervals, f.properties.ward_id, f.properties.rank),
        ...(wantGeometry ? { geom_geojson: f.geometry } : {}),
      }));
    return jsonResponse({ source: "snapshot", count: wards.length, wards });
  } catch {
    return errorResponse(503, "Ward data is temporarily unavailable.");
  }
}
