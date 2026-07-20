"use client";

import { useEffect, useMemo, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { ArrowLeft, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import CoefficientSparkline from "./CoefficientSparkline";
import Citation from "./Citation";
import { matchCitationFromText } from "@/lib/citations";
import { areasForWard } from "@/lib/wardAreas";

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

function hviBandColor(hvi: number | null): string {
  if (hvi === null) return "#cccccc";
  if (hvi < 20) return "#ffffb2";
  if (hvi < 35) return "#fed976";
  if (hvi < 50) return "#feb24c";
  if (hvi < 65) return "#fd8d3c";
  if (hvi < 80) return "#f03b20";
  return "#bd0026";
}

export default function WardPanel({
  selectedWardId,
  onSelectWard,
}: {
  selectedWardId: string | null;
  onSelectWard: (wardId: string | null) => void;
}) {
  const [wards, setWards] = useState<Feature<Geometry, WardProps>[] | null>(null);
  const [recs, setRecs] = useState<NbsRec[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

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

  const filtered = useMemo(() => {
    if (!wards) return [];
    const q = search.trim().toLowerCase();
    if (!q) return wards;
    return wards.filter((f) => f.properties.ward_id.toLowerCase().includes(q));
  }, [wards, search]);

  const selected = wards?.find((f) => f.properties.ward_id === selectedWardId) ?? null;
  const selectedRecs = selected
    ? (recs ?? []).filter((r) => r.ward_id === selected.properties.ward_id).sort((a, b) => a.priority - b.priority)
    : [];

  if (error) return <div className="p-4 text-sm text-destructive">Failed to load ward data: {error}</div>;
  if (!wards || !recs) return <div className="p-4 text-sm text-muted-foreground">Loading wards…</div>;

  if (selected) {
    const p = selected.properties;
    const areas = areasForWard(p.ward_id);
    return (
      <div className="flex h-full min-h-0 flex-col">
        <div className="border-b border-border px-4 py-3">
          <Button variant="ghost" size="sm" onClick={() => onSelectWard(null)} className="-ml-2 text-muted-foreground">
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
            All 24 wards
          </Button>
        </div>
        <ScrollArea className="min-h-0 flex-1">
          <div className="p-4">
            <div className="flex items-baseline justify-between">
              <div className="flex items-center gap-2">
                <Badge
                  className="h-7 w-7 justify-center rounded-full p-0 text-xs font-semibold text-black/80"
                  style={{ background: hviBandColor(p.HVI) }}
                >
                  {p.rank}
                </Badge>
                <span className="text-lg font-semibold text-foreground">Ward {p.ward_id}</span>
              </div>
              <span className="font-mono text-sm text-muted-foreground">HVI {p.HVI?.toFixed(1)}</span>
            </div>

            <p className="mt-1 text-xs text-muted-foreground">
              Priority {p.rank} of 24 &middot; {p.n_cells ?? "n/a"} grid cells
            </p>
            {areas.length > 0 && (
              <p className="mt-1.5 text-xs text-muted-foreground">
                <span className="text-foreground/80">Areas:</span> {areas.join(", ")}
              </p>
            )}

            <div className="mt-4 space-y-2">
              {FACTORS.map((f2) => (
                <CoefficientSparkline
                  key={String(f2.key)}
                  label={f2.label}
                  value={(p[f2.key] as number | null) ?? 0}
                  max={CONTRIB_BAR_MAX}
                />
              ))}
            </div>
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              Red pushes this ward&apos;s score up, green pushes it down, compared to the city average.
            </p>

            {selectedRecs.length > 0 && (
              <div className="mt-5">
                <p className="kicker">Recommended interventions</p>
                <div className="mt-2 space-y-2">
                  {selectedRecs.map((rec) => {
                    const cited = matchCitationFromText(rec.citation);
                    return (
                      <Card key={rec.intervention + rec.priority} size="sm">
                        <CardContent className="text-xs">
                          <span className="font-medium text-foreground">{rec.intervention}</span>
                          <p className="mt-0.5 text-muted-foreground">{rec.rationale}</p>
                          {cited ? (
                            <div className="mt-1.5">
                              <Citation mode="chip" entry={cited} />
                            </div>
                          ) : (
                            <p className="mt-0.5 italic text-muted-foreground">{rec.citation}</p>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">24 wards, ranked by heat vulnerability</h2>
        <p className="mt-1 text-xs leading-snug text-muted-foreground">
          Click a ward, or click one on the map, to see the full breakdown and recommendation.
        </p>
        <div className="relative mt-2">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            type="text"
            id="ward-search"
            name="ward-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find a ward…"
            className="pl-8"
          />
        </div>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        <div className="divide-y divide-border">
          {filtered.map((f) => {
            const p = f.properties;
            return (
              <button
                key={p.ward_id}
                onClick={() => onSelectWard(p.ward_id)}
                title={areasForWard(p.ward_id).join(", ")}
                className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left transition-colors hover:bg-accent"
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <span className="w-5 shrink-0 text-right font-mono text-xs text-muted-foreground">{p.rank}</span>
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-sm"
                    style={{ background: hviBandColor(p.HVI) }}
                    aria-hidden
                  />
                  <span className="truncate text-sm font-medium text-foreground">Ward {p.ward_id}</span>
                </div>
                <span className="shrink-0 font-mono text-xs text-muted-foreground">{p.HVI?.toFixed(1)}</span>
              </button>
            );
          })}
          {filtered.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No ward matches &quot;{search}&quot;.</p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
