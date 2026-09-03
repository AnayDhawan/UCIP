/**
 * GET /api/v1/cells?ward=&bbox=&limit=&geometry=
 *
 * The 1 km analysis grid: the per-cell measurements the ward scores are built
 * from. This is the endpoint for anyone who wants to check the working rather
 * than take the ward rollup on trust.
 *
 * Geometry is off by default. All 541 cell polygons is roughly a megabyte, and
 * most consumers want the indicator values, not the squares.
 */

import type { FeatureCollection, Geometry } from "geojson";
import { boundsOf } from "@/lib/geometry";
import {
  errorResponse,
  jsonResponse,
  normaliseWardId,
  optionsResponse,
  parseLimit,
  readSnapshot,
  supabase,
} from "../_lib";

export const revalidate = 3600;

const CELL_COLUMNS =
  "grid_id,ward_id,lst_c,ndvi,ndvi_prev,pop_density_km2,elderly_pct,slum_pct," +
  "hospital_dist_m,impervious_pct,hvi,plantable,worldcover_class";

type Bbox = [number, number, number, number];

/** Parses "minLon,minLat,maxLon,maxLat", the order every GIS tool uses. */
function parseBbox(raw: string | null): Bbox | null | "invalid" {
  if (!raw) return null;
  const parts = raw.split(",").map(Number);
  if (parts.length !== 4 || parts.some((n) => !Number.isFinite(n))) return "invalid";
  const [minLon, minLat, maxLon, maxLat] = parts;
  if (minLon > maxLon || minLat > maxLat) return "invalid";
  return [minLon, minLat, maxLon, maxLat];
}

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limit = parseLimit(url.searchParams.get("limit"), 541, 1000);
  const wantGeometry = url.searchParams.get("geometry") === "true";
  const rawWard = url.searchParams.get("ward");

  const bbox = parseBbox(url.searchParams.get("bbox"));
  if (bbox === "invalid") {
    return errorResponse(
      400,
      "'bbox' must be four numbers: minLon,minLat,maxLon,maxLat.",
      "Example: bbox=72.80,19.00,72.95,19.15"
    );
  }

  let wardId: string | null = null;
  if (rawWard !== null) {
    wardId = normaliseWardId(rawWard);
    if (!wardId) return errorResponse(400, `'${rawWard}' is not a valid BMC ward code.`);
  }

  // The database has no bbox filter without PostGIS-aware querying, so a bbox
  // request goes to the snapshot, where the geometry is present anyway.
  const db = bbox ? null : supabase();
  if (db) {
    let query = db
      .from("grid_cells")
      .select(wantGeometry ? `${CELL_COLUMNS},geom_geojson` : CELL_COLUMNS)
      .order("grid_id", { ascending: true })
      .limit(limit);
    if (wardId) query = query.eq("ward_id", wardId);

    const { data, error } = await query;
    if (!error && data) {
      return jsonResponse({ source: "database", count: data.length, cells: data });
    }
  }

  try {
    const geo = await readSnapshot<FeatureCollection<Geometry, Record<string, unknown>>>(
      "cells_nbs.geojson"
    );

    const cells = geo.features
      .filter((f) => !wardId || f.properties.ward_id === wardId)
      .filter((f) => {
        if (!bbox) return true;
        const b = boundsOf(f.geometry);
        if (!b) return false;
        const [[minLat, minLon], [maxLat, maxLon]] = b;
        // Overlap, not containment: a cell straddling the edge is still in view.
        return !(maxLon < bbox[0] || minLon > bbox[2] || maxLat < bbox[1] || minLat > bbox[3]);
      })
      .slice(0, limit)
      .map((f) => ({
        ...f.properties,
        ...(wantGeometry ? { geom_geojson: f.geometry } : {}),
      }));

    return jsonResponse({ source: "snapshot", count: cells.length, cells });
  } catch {
    return errorResponse(503, "Cell data is temporarily unavailable.");
  }
}
