"use client";

import { useEffect, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";

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

const BAR_SCALE = 0.3; // contribution values (weight x z-score) mostly fall in [-0.3, 0.3]

function ContribBar({ label, value }: { label: string; value: number | null }) {
  const v = value ?? 0;
  const pct = Math.min(Math.abs(v) / BAR_SCALE, 1) * 50;
  const positive = v >= 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-32 shrink-0 text-zinc-600 dark:text-zinc-400">{label}</span>
      <div className="relative h-3 flex-1 bg-zinc-100 dark:bg-zinc-800">
        <div className="absolute inset-y-0 left-1/2 w-px bg-zinc-400" />
        <div
          className={`absolute inset-y-0 ${positive ? "bg-red-400" : "bg-emerald-400"}`}
          style={
            positive
              ? { left: "50%", width: `${pct}%` }
              : { right: "50%", width: `${pct}%` }
          }
        />
      </div>
    </div>
  );
}

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

  if (error) return <div className="p-4 text-sm text-red-600">Failed to load ward data: {error}</div>;
  if (!wards || !recs) return <div className="p-4 text-sm text-zinc-500">Loading ward cards…</div>;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-900/10 px-4 py-3 dark:border-white/10">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          24 wards, ranked by heat vulnerability
        </h2>
        <p className="mt-1 text-xs leading-snug text-zinc-600 dark:text-zinc-400">
          Bars show what pushes a ward&apos;s score up (red) or down (green) compared to the city
          average. Each card ends with the top recommended intervention. Scroll for all 24.
        </p>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-zinc-200 dark:divide-zinc-800">
      {wards.map((f) => {
        const p = f.properties;
        const wardRecs = recs
          .filter((r) => r.ward_id === p.ward_id)
          .sort((a, b) => a.priority - b.priority);
        const topRec = wardRecs[0];
        return (
          <div key={p.ward_id} className="p-4">
            <div className="flex items-baseline justify-between">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-zinc-800 text-xs font-medium text-white dark:bg-zinc-200 dark:text-black">
                  {p.rank}
                </span>
                <span className="font-semibold text-black dark:text-zinc-50">Ward {p.ward_id}</span>
              </div>
              <span className="text-sm text-zinc-600 dark:text-zinc-400">HVI {p.HVI?.toFixed(1)}</span>
            </div>
            <div className="mt-2 space-y-1">
              {FACTORS.map((f2) => (
                <ContribBar key={String(f2.key)} label={f2.label} value={p[f2.key] as number | null} />
              ))}
            </div>
            {topRec && (
              <div className="mt-2 rounded bg-zinc-50 p-2 text-xs dark:bg-zinc-900">
                <span className="font-medium text-black dark:text-zinc-50">{topRec.intervention}</span>
                <p className="mt-0.5 text-zinc-600 dark:text-zinc-400">{topRec.rationale}</p>
                <p className="mt-0.5 italic text-zinc-500">{topRec.citation}</p>
              </div>
            )}
          </div>
        );
      })}
      </div>
    </div>
  );
}
