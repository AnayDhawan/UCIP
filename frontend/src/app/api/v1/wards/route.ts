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
  supabase,
} from "../_lib";

export const revalidate = 3600;

type WardRow = {
  ward_id: string;
  hvi: number | null;
  rank: number | null;
  n_cells: number | null;
  contrib: Record<string, number> | null;
};

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
  };
}

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limit = parseLimit(url.searchParams.get("limit"), 24, 24);
  const wantGeometry = url.searchParams.get("geometry") === "true";

  const db = supabase();
  if (db) {
    const columns = wantGeometry
      ? "ward_id,hvi,rank,n_cells,contrib,geom_geojson"
      : "ward_id,hvi,rank,n_cells,contrib";
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
