"use client";

import { useEffect, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { NbsRec, WardProps } from "./wardTypes";
import { WARD_PROFILES_URL, type WardProfileData } from "./wardProfile";

/**
 * Everything the ward surfaces read, fetched once per consumer.
 *
 * The sidebar detail view and the fullscreen/mobile dialog show the same ward
 * from the same three files; keeping the loading in one hook stops their fetch
 * logic, sort order and error handling from drifting apart the way the old
 * per-component copies did.
 */
export type WardData = {
  /** Sorted by rank, most vulnerable first. */
  wards: Feature<Geometry, WardProps>[] | null;
  recs: NbsRec[] | null;
  profiles: WardProfileData | null;
  error: string | null;
};

/** A ward row as the API returns it: lowercase keys and a nested contrib object. */
type ApiWard = {
  ward_id: string;
  hvi: number | null;
  rank: number | null;
  n_cells: number | null;
  contrib: Record<string, number> | null;
  geom_geojson?: Geometry;
};

/**
 * Reshapes an API ward back into the GeoJSON feature the components expect.
 *
 * The snapshot uses SCREAMING keys (`HVI`) and flat `contrib_*` fields because
 * that is what geopandas wrote; the API normalises them. Converting here rather
 * than changing every consumer keeps the change to the data layer, which is what
 * issue #53 is about.
 */
function apiWardToFeature(w: ApiWard): Feature<Geometry, WardProps> {
  const props: Record<string, unknown> = {
    ward_id: w.ward_id,
    HVI: w.hvi,
    rank: w.rank,
    n_cells: w.n_cells,
  };
  for (const [key, value] of Object.entries(w.contrib ?? {})) {
    props[`contrib_${key}`] = value;
  }
  return {
    type: "Feature",
    geometry: (w.geom_geojson ?? null) as Geometry,
    properties: props as WardProps,
  };
}

async function fetchWards(): Promise<Feature<Geometry, WardProps>[]> {
  try {
    const res = await fetch("/api/v1/wards?geometry=true");
    if (!res.ok) throw new Error(`wards ${res.status}`);
    const json = (await res.json()) as { wards: ApiWard[] };
    const features = json.wards.map(apiWardToFeature);
    // A ward with no geometry cannot be drawn. If the API somehow returns rows
    // without it, fall through to the snapshot rather than render an empty map.
    if (features.length === 0 || features.some((f) => !f.geometry)) {
      throw new Error("wards response carried no geometry");
    }
    return features;
  } catch {
    const geo = (await fetch("/wards_hvi.geojson").then((r) =>
      r.json()
    )) as FeatureCollection<Geometry, WardProps>;
    return geo.features;
  }
}

export function useWardData(): WardData {
  const [wards, setWards] = useState<Feature<Geometry, WardProps>[] | null>(null);
  const [recs, setRecs] = useState<NbsRec[] | null>(null);
  const [profiles, setProfiles] = useState<WardProfileData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      // Ward scores come from the API, which reads live Supabase and falls back
      // to the same snapshot file this used to fetch directly (issue #53). That
      // means a pipeline refresh reaches readers without a rebuild, while a
      // database outage degrades to slightly older numbers instead of an empty
      // dashboard. `geometry=true` because the map needs the polygons.
      //
      // Deliberately NOT retiring the snapshot path, which is what the issue
      // originally proposed. Two reasons. The static files are the demo-safe
      // mode that kept this site working through the Supabase project being
      // deleted in September 2026, and the issue's second rationale, that
      // accounts would be hard to bolt onto build-time-frozen files, no longer
      // applies now that #59/#60/#62 were closed in favour of URL-based ward
      // tracking. Live-first with a static floor keeps the freshness without
      // giving up the resilience.
      fetchWards(),
      fetch("/api/v1/recommendations?limit=500")
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`recommendations ${r.status}`))))
        .then((json: { recommendations: NbsRec[] }) => json.recommendations)
        .catch(() => fetch("/nbs_recommendations.json").then((r) => r.json() as Promise<NbsRec[]>)),
    ])
      .then(([wardFeatures, recsData]) => {
        if (cancelled) return;
        setWards(
          [...wardFeatures].sort((a, b) => (a.properties.rank ?? 99) - (b.properties.rank ?? 99))
        );
        setRecs(recsData);
      })
      .catch((err) => {
        if (!cancelled) setError(String(err));
      });

    // The descriptive profile is additive: without it a ward still shows its
    // score, breakdown and interventions, so a failure here must not block them.
    fetch(WARD_PROFILES_URL)
      .then((r) => (r.ok ? (r.json() as Promise<WardProfileData>) : null))
      .then((json) => {
        if (!cancelled && json) setProfiles(json);
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, []);

  return { wards, recs, profiles, error };
}
