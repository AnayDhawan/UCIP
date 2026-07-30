"use client";

import { useEffect, useMemo, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { areasForWard } from "@/lib/wardAreas";
import { hviColor } from "@/lib/hvi";
import type { WardProps } from "@/lib/wardTypes";

/**
 * The ranked ward list.
 *
 * This used to be a master-detail panel, with a whole second view for the
 * selected ward. That detail view now lives in WardDialog, which works on every
 * viewport and in fullscreen, where this `hidden md:block` aside does not
 * exist at all. What remains here is the list: the browsable, searchable index
 * into the map.
 */

export default function WardPanel({
  selectedWardId,
  onSelectWard,
}: {
  selectedWardId: string | null;
  onSelectWard: (wardId: string | null) => void;
}) {
  const [wards, setWards] = useState<Feature<Geometry, WardProps>[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/wards_hvi.geojson")
      .then((r) => r.json() as Promise<FeatureCollection<Geometry, WardProps>>)
      .then((wardsData) => {
        const sorted = [...wardsData.features].sort(
          (a, b) => (a.properties.rank ?? 99) - (b.properties.rank ?? 99)
        );
        setWards(sorted);
      })
      .catch((err) => setError(String(err)));
  }, []);

  const filtered = useMemo(() => {
    if (!wards) return [];
    const q = search.trim().toLowerCase();
    if (!q) return wards;
    return wards.filter((f) => {
      const wardId = f.properties.ward_id.toLowerCase();
      const areas = areasForWard(f.properties.ward_id).join(" ").toLowerCase();
      return wardId.includes(q) || areas.includes(q);
    });
  }, [wards, search]);

  if (error) return <div className="p-4 text-sm text-destructive">Failed to load ward data: {error}</div>;
  if (!wards) return <div className="p-4 text-sm text-muted-foreground">Loading wards…</div>;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">24 wards, ranked by heat vulnerability</h2>
        <p className="mt-1 text-xs leading-snug text-muted-foreground">
          Click a ward, here or on the map, to open its full profile.
        </p>
        <div className="relative mt-2">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            type="text"
            id="ward-search"
            name="ward-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find a ward or area…"
            className="pl-8"
          />
        </div>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        <div className="divide-y divide-border">
          {filtered.map((f) => {
            const p = f.properties;
            // Selection no longer swaps this panel's view, so the row itself has
            // to show which ward the map and dialog are on.
            const isSelected = p.ward_id === selectedWardId;
            return (
              <button
                key={p.ward_id}
                onClick={() => onSelectWard(p.ward_id)}
                title={areasForWard(p.ward_id).join(", ")}
                aria-current={isSelected ? "true" : undefined}
                className={`flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left transition-colors hover:bg-accent ${
                  isSelected ? "bg-accent" : ""
                }`}
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <span className="w-5 shrink-0 text-right font-mono text-xs text-muted-foreground">{p.rank}</span>
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-sm"
                    style={{ background: hviColor(p.HVI) }}
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
