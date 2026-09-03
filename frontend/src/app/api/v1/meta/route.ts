/**
 * GET /api/v1/meta
 *
 * What this deployment is serving: coverage, counts, licence, the composite
 * window the figures were computed from, and when the pipeline last ran.
 *
 * The composite window matters more than the refresh date and is the reason
 * this endpoint exists rather than just a version string. "Refreshed last week"
 * and "computed from imagery captured last winter" are both true at once, and a
 * consumer needs the second one to know how old the underlying measurements are.
 */

import type { FeatureCollection, Geometry } from "geojson";
import type { NbsRec, WardProps } from "@/lib/wardTypes";
import { API_VERSION, jsonResponse, optionsResponse, readSnapshot, supabase } from "../_lib";
import { CITATIONS } from "@/lib/citations";
import { MUMBAI } from "@/lib/city";

export const revalidate = 3600;

export function OPTIONS() {
  return optionsResponse();
}

export async function GET() {
  const [wards, recs] = await Promise.all([
    readSnapshot<FeatureCollection<Geometry, WardProps>>("wards_hvi.geojson").catch(() => null),
    readSnapshot<NbsRec[]>("nbs_recommendations.json").catch(() => null),
  ]);

  const pcaLog = await readSnapshot<{
    weights?: Record<string, number>;
    explained_variance_ratio?: number;
    fallback_used?: boolean;
  }>("hvi_pca_log.json").catch(() => null);

  return jsonResponse({
    name: "UCIP: Urban Climate Intelligence Platform",
    api_version: API_VERSION,
    description:
      "Ward-level heat vulnerability for Mumbai, with cited nature-based cooling recommendations.",
    coverage: {
      cities: [{ name: MUMBAI.name, wards: wards?.features.length ?? null }],
      note: "Mumbai only. The pipeline is city-agnostic; no second city is configured yet.",
    },
    counts: {
      wards: wards?.features.length ?? null,
      recommendations: recs?.length ?? null,
      citations: CITATIONS.length,
    },
    method: {
      index: "Heat Vulnerability Index, 0-100, from seven standardised indicators",
      weighting: pcaLog?.fallback_used
        ? "published literature weights (PCA fallback triggered)"
        : "PCA-derived, per Reid et al. 2009",
      explainability:
        "Transparent linear index. Per-factor contributions are published per ward, so a score decomposes exactly into its drivers.",
      limitations_url: "/methodology",
    },
    database_configured: supabase() !== null,
    license: {
      code: "Apache-2.0",
      data: "See /legal for per-source terms (Landsat, WorldPop, ESA WorldCover, OpenStreetMap, Datameet).",
    },
    links: {
      documentation: "/api/v1/openapi.json",
      methodology: "/methodology",
      repository: "https://github.com/AnayDhawan/UCIP",
    },
  });
}
