/**
 * GET /api/v1/wards/{wardId}
 *
 * One ward, with its index, rank, factor breakdown and its ranked
 * nature-based-solution recommendations, each carrying the paper it cites.
 *
 * Ward ids contain a slash for split wards (F/N, G/S, R/C), so they must be URL
 * encoded: /api/v1/wards/F%2FN
 */

import type { FeatureCollection, Geometry } from "geojson";
import type { NbsRec, WardProps } from "@/lib/wardTypes";
import {
  errorResponse,
  jsonResponse,
  normaliseWardId,
  optionsResponse,
  readSnapshot,
  supabase,
} from "../../_lib";

export const revalidate = 3600;

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ wardId: string }> }
) {
  const { wardId: raw } = await params;
  const wardId = normaliseWardId(raw);
  if (!wardId) {
    return errorResponse(
      400,
      `'${raw}' is not a valid BMC ward code.`,
      "Codes are one or two letters, optionally with a suffix after a slash, for example A, L, or F/N (URL-encoded as F%2FN)."
    );
  }

  const db = supabase();
  if (db) {
    const [wardResult, recsResult] = await Promise.all([
      db.from("wards").select("ward_id,hvi,rank,n_cells,contrib").eq("ward_id", wardId).maybeSingle(),
      db
        .from("nbs_recommendations")
        .select("intervention,rationale,citation,priority,cell_count")
        .eq("ward_id", wardId)
        .order("priority", { ascending: true }),
    ]);

    if (!wardResult.error && wardResult.data) {
      return jsonResponse({
        source: "database",
        ward: wardResult.data,
        recommendations: recsResult.data ?? [],
      });
    }
    // A clean query that found nothing is a real 404, not a reason to fall back.
    if (!wardResult.error && wardResult.data === null) {
      return errorResponse(404, `No ward '${wardId}'.`, "See /api/v1/wards for the 24 valid codes.");
    }
  }

  try {
    const [geo, recs] = await Promise.all([
      readSnapshot<FeatureCollection<Geometry, WardProps>>("wards_hvi.geojson"),
      readSnapshot<NbsRec[]>("nbs_recommendations.json"),
    ]);
    const feature = geo.features.find((f) => f.properties.ward_id === wardId);
    if (!feature) {
      return errorResponse(404, `No ward '${wardId}'.`, "See /api/v1/wards for the 24 valid codes.");
    }

    const p = feature.properties;
    const contrib: Record<string, number> = {};
    for (const [key, value] of Object.entries(p)) {
      if (key.startsWith("contrib_") && typeof value === "number") {
        contrib[key.slice("contrib_".length)] = value;
      }
    }

    return jsonResponse({
      source: "snapshot",
      ward: {
        ward_id: p.ward_id,
        hvi: p.HVI,
        rank: p.rank,
        n_cells: p.n_cells,
        contrib: Object.keys(contrib).length ? contrib : null,
      },
      recommendations: recs
        .filter((r) => r.ward_id === wardId)
        .sort((a, b) => a.priority - b.priority),
    });
  } catch {
    return errorResponse(503, "Ward data is temporarily unavailable.");
  }
}
