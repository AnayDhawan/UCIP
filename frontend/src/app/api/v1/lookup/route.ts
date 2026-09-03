/**
 * GET /api/v1/lookup?lat=&lon=
 *
 * Resolves a coordinate to the ward that contains it, with that ward's index,
 * rank and top recommendation.
 *
 * This is the endpoint a non-expert actually wants. Everything else UCIP
 * publishes is keyed by BMC ward code, which assumes you already know your ward;
 * almost nobody does. "What is the heat risk where I am" is the question, and
 * this is the answer.
 *
 * Prefers the PostGIS ward_at() function from
 * supabase/migrations/0006_postgis_geometry.sql, which does the containment test
 * in the database against a GiST index. Falls back to a point-in-polygon test
 * over the committed ward snapshot when that migration has not been applied or
 * the database is unavailable, so the endpoint works either way.
 */

import type { FeatureCollection, Geometry, Polygon, MultiPolygon, Position } from "geojson";
import type { NbsRec, WardProps } from "@/lib/wardTypes";
import {
  errorResponse,
  jsonResponse,
  optionsResponse,
  parseCoordinate,
  readSnapshot,
  supabase,
} from "../_lib";

export const revalidate = 3600;

/**
 * Ray-casting point-in-polygon over one ring.
 *
 * GeoJSON positions are [lng, lat]; the caller passes them in that order too, so
 * the axes are never swapped mid-algorithm. Points exactly on an edge are not
 * guaranteed either way, which is acceptable: ward boundaries follow roads, and
 * a coordinate landing precisely on one is arbitrary anyway.
 */
function pointInRing(point: Position, ring: Position[]): boolean {
  const [x, y] = point;
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const intersects = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

/** True when the point is inside the polygon's exterior ring and outside its holes. */
function pointInPolygon(point: Position, rings: Position[][]): boolean {
  if (rings.length === 0 || !pointInRing(point, rings[0])) return false;
  for (let i = 1; i < rings.length; i++) {
    if (pointInRing(point, rings[i])) return false;
  }
  return true;
}

function geometryContains(geometry: Geometry, point: Position): boolean {
  if (geometry.type === "Polygon") {
    return pointInPolygon(point, (geometry as Polygon).coordinates);
  }
  if (geometry.type === "MultiPolygon") {
    return (geometry as MultiPolygon).coordinates.some((poly) => pointInPolygon(point, poly));
  }
  return false;
}

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const lat = parseCoordinate(url.searchParams.get("lat"), -90, 90);
  const lon = parseCoordinate(url.searchParams.get("lon"), -180, 180);

  if (lat === null || lon === null) {
    return errorResponse(
      400,
      "Both 'lat' and 'lon' are required and must be valid coordinates.",
      "Example: /api/v1/lookup?lat=19.076&lon=72.877"
    );
  }

  const notFound = () =>
    errorResponse(
      404,
      `No ward contains ${lat}, ${lon}.`,
      "UCIP currently covers the 24 BMC wards of Mumbai only."
    );

  const db = supabase();
  if (db) {
    const { data, error } = await db.rpc("ward_at", { lat, lon });
    if (!error && Array.isArray(data)) {
      if (data.length === 0) return notFound();
      const ward = data[0] as { ward_id: string };
      const { data: recs } = await db
        .from("nbs_recommendations")
        .select("intervention,rationale,citation,priority")
        .eq("ward_id", ward.ward_id)
        .order("priority", { ascending: true })
        .limit(1);
      return jsonResponse({
        source: "database",
        query: { lat, lon },
        ward,
        top_recommendation: recs?.[0] ?? null,
      });
    }
    // error here usually means migration 0006 has not been applied yet; fall
    // through to the snapshot rather than failing the request.
  }

  try {
    const [geo, allRecs] = await Promise.all([
      readSnapshot<FeatureCollection<Geometry, WardProps>>("wards_hvi.geojson"),
      readSnapshot<NbsRec[]>("nbs_recommendations.json"),
    ]);

    const point: Position = [lon, lat];
    const feature = geo.features.find((f) => geometryContains(f.geometry, point));
    if (!feature) return notFound();

    const p = feature.properties;
    const top = allRecs
      .filter((r) => r.ward_id === p.ward_id)
      .sort((a, b) => a.priority - b.priority)[0];

    return jsonResponse({
      source: "snapshot",
      query: { lat, lon },
      ward: { ward_id: p.ward_id, hvi: p.HVI, rank: p.rank, n_cells: p.n_cells },
      top_recommendation: top
        ? {
            intervention: top.intervention,
            rationale: top.rationale,
            citation: top.citation,
            priority: top.priority,
          }
        : null,
    });
  } catch {
    return errorResponse(503, "Ward data is temporarily unavailable.");
  }
}
