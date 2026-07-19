"use client";

import { useEffect, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import CoefficientSparkline from "./CoefficientSparkline";
import Citation from "./Citation";
import { matchCitationFromText } from "@/lib/citations";

type WardProps = {
  ward_id: string;
  ward_gid: number;
  HVI: number | null;
  rank: number | null;
  n_cells: number | null;
  contrib_LST_C: number | null;
  contrib_NDVI: number | null;
  contrib_pop_density_km2: number | null;
  contrib_elderly_pct: number | null;
  contrib_slum_pct: number | null;
  contrib_hospital_dist_m: number | null;
  contrib_impervious_pct: number | null;
  [key: string]: unknown;
};

type NbsRec = {
  ward_id: string;
  intervention: string;
  rationale: string;
  citation: string;
  priority: number;
  cell_count: number;
};

const FACTORS: { key: keyof WardProps; label: string }[] = [
  { key: "contrib_LST_C", label: "Land surface temp" },
  { key: "contrib_NDVI", label: "Green cover (NDVI)" },
  { key: "contrib_pop_density_km2", label: "Population density" },
  { key: "contrib_elderly_pct", label: "Elderly %" },
  { key: "contrib_slum_pct", label: "Slum index" },
  { key: "contrib_hospital_dist_m", label: "Hospital distance" },
  { key: "contrib_impervious_pct", label: "Impervious / built-up" },
];

const CONTRIB_BAR_MAX = 0.3; // contribution values (weight x z-score) mostly fall in [-0.3, 0.3]

export default function WardCards() {
  const [wards, setWards] = useState<Feature<Geometry, WardProps>[] | null>(null);
  const [recs, setRecs] = useState<NbsRec[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/wards_hvi.geojson").then((r) => r.json() as Promise<FeatureCollection<Geometry, WardProps>>),
      fetch("/nbs_recommendations.json").then((r) => r.json() as Promise<NbsRec[]>),
    ])
      .then(([wardsData, recsData]) => {
        const sorted = [...wardsData.features].sort((a, b) => (a.properties.rank ?? 99) - (b.properties.rank ?? 99));
        setWards(sorted);
        setRecs(recsData);
      })
      .catch((err) => setError(String(err)));
  }, []);

  if (error) return <div className="p-4 text-sm text-red-500">Failed to load ward data: {error}</div>;
  if (!wards || !recs) return <div className="p-4 text-sm text-muted-foreground">Loading ward cards…</div>;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">24 wards, ranked by heat vulnerability</h2>
        <p className="mt-1 text-xs leading-snug text-muted-foreground">
          Bars show what pushes a ward&apos;s score up (red) or down (green) compared to the city
          average. Each card ends with the top recommended intervention. Scroll for all 24.
        </p>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-border">
        {wards.map((f) => {
          const p = f.properties;
          const wardRecs = recs
            .filter((r) => r.ward_id === p.ward_id)
            .sort((a, b) => a.priority - b.priority);
          const topRec = wardRecs[0];
          const matchedCitation = topRec ? matchCitationFromText(topRec.citation) : undefined;
          return (
            <div key={p.ward_id} className="p-4">
              <div className="flex items-baseline justify-between">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-brand-teal text-xs font-medium text-white">
                    {p.rank}
                  </span>
                  <span className="font-semibold text-foreground">Ward {p.ward_id}</span>
                </div>
                <span className="text-sm text-muted-foreground">HVI {p.HVI?.toFixed(1)}</span>
              </div>
              <div className="mt-2 space-y-1">
                {FACTORS.map((f2) => (
                  <CoefficientSparkline
                    key={String(f2.key)}
                    label={f2.label}
                    value={(p[f2.key] as number | null) ?? 0}
                    max={CONTRIB_BAR_MAX}
                  />
                ))}
              </div>
              {topRec && (
                <div className="mt-2 rounded bg-muted p-2 text-xs">
                  <span className="font-medium text-foreground">{topRec.intervention}</span>
                  <p className="mt-0.5 text-muted-foreground">{topRec.rationale}</p>
                  {matchedCitation ? (
                    <div className="mt-1.5">
                      <Citation mode="chip" entry={matchedCitation} />
                    </div>
                  ) : (
                    <p className="mt-0.5 italic text-muted-foreground">{topRec.citation}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
