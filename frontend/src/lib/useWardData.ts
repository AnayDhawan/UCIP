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

export function useWardData(): WardData {
  const [wards, setWards] = useState<Feature<Geometry, WardProps>[] | null>(null);
  const [recs, setRecs] = useState<NbsRec[] | null>(null);
  const [profiles, setProfiles] = useState<WardProfileData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      fetch("/wards_hvi.geojson").then(
        (r) => r.json() as Promise<FeatureCollection<Geometry, WardProps>>
      ),
      fetch("/nbs_recommendations.json").then((r) => r.json() as Promise<NbsRec[]>),
    ])
      .then(([wardsData, recsData]) => {
        if (cancelled) return;
        setWards(
          [...wardsData.features].sort(
            (a, b) => (a.properties.rank ?? 99) - (b.properties.rank ?? 99)
          )
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
