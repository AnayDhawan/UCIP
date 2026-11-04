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
import { WARD_COLUMNS, fromSnapshot } from "../../_ward";
import {
  errorResponse,
  intervalFields,
  jsonResponse,
  normaliseWardId,
  optionsResponse,
  rateLimited,
  readIntervals,
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
  const limited = await rateLimited(request);
  if (limited) return limited;

  const { wardId: raw } = await params;
  const wardId = normaliseWardId(raw);
  if (!wardId) {
    return errorResponse(
      400,
      `'${raw}' is not a valid BMC ward code.`,
      "Codes are one or two letters, optionally with a suffix after a slash, for example A, L, or F/N (URL-encoded as F%2FN)."
    );
  }

  const intervals = await readIntervals();

  const db = supabase();
  if (db) {
    const [wardResult, recsResult] = await Promise.all([
      db.from("wards").select(WARD_COLUMNS).eq("ward_id", wardId).maybeSingle(),
      db
        .from("nbs_recommendations")
        .select("intervention,rationale,citation,priority,cell_count")
        .eq("ward_id", wardId)
        .order("priority", { ascending: true }),
    ]);

    if (!wardResult.error && wardResult.data) {
      return jsonResponse({
        source: "database",
        ward: { ...wardResult.data, ...intervalFields(intervals, wardId, wardResult.data.rank) },
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

    return jsonResponse({
      source: "snapshot",
      ward: {
        ...fromSnapshot(p),
        ...intervalFields(intervals, wardId, p.rank),
      },
      recommendations: recs
        .filter((r) => r.ward_id === wardId)
        .sort((a, b) => a.priority - b.priority),
    });
  } catch {
    return errorResponse(503, "Ward data is temporarily unavailable.");
  }
}
