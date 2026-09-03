/**
 * GET /api/v1/recommendations?ward=&limit=
 *
 * Nature-based-solution recommendations, ranked by priority. Every row carries
 * the rationale that fired the rule and the paper it cites, because a
 * recommendation without its reasoning is just an opinion.
 */

import type { NbsRec } from "@/lib/wardTypes";
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

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const rawWard = url.searchParams.get("ward");
  const limit = parseLimit(url.searchParams.get("limit"), 200, 500);

  let wardId: string | null = null;
  if (rawWard !== null) {
    wardId = normaliseWardId(rawWard);
    if (!wardId) {
      return errorResponse(400, `'${rawWard}' is not a valid BMC ward code.`);
    }
  }

  const db = supabase();
  if (db) {
    let query = db
      .from("nbs_recommendations")
      .select("ward_id,intervention,rationale,citation,priority,cell_count")
      .order("ward_id", { ascending: true })
      .order("priority", { ascending: true })
      .limit(limit);
    if (wardId) query = query.eq("ward_id", wardId);

    const { data, error } = await query;
    if (!error && data) {
      return jsonResponse({ source: "database", count: data.length, recommendations: data });
    }
  }

  try {
    const all = await readSnapshot<NbsRec[]>("nbs_recommendations.json");
    const rows = all
      .filter((r) => !wardId || r.ward_id === wardId)
      .sort((a, b) => a.ward_id.localeCompare(b.ward_id) || a.priority - b.priority)
      .slice(0, limit);
    return jsonResponse({ source: "snapshot", count: rows.length, recommendations: rows });
  } catch {
    return errorResponse(503, "Recommendation data is temporarily unavailable.");
  }
}
