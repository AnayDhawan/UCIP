"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { areasForWard } from "@/lib/wardAreas";
import { hviColor } from "@/lib/hvi";
import { useWardData } from "@/lib/useWardData";
import WardDetail from "./WardDetail";
import WardDetailHeader from "./WardDetailHeader";

/**
 * The dashboard sidebar: a ranked, searchable ward list that hands the whole
 * panel over to the selected ward's profile.
 *
 * Selecting a ward replaces the list rather than opening something on top of
 * the map, so the choropleth stays fully visible and clickable while a ward is
 * being read. The X returns to the list. Fullscreen and viewports below `md`
 * have no sidebar to hand over, so those use WardDialog instead.
 */

export default function WardPanel({
  selectedWardId,
  onSelectWard,
}: {
  selectedWardId: string | null;
  onSelectWard: (wardId: string | null) => void;
}) {
  const { wards, recs, profiles, error } = useWardData();
  const [search, setSearch] = useState("");

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

  const selected = wards.find((f) => f.properties.ward_id === selectedWardId) ?? null;

  if (selected) {
    const props = selected.properties;
    const wardRecs = (recs ?? [])
      .filter((r) => r.ward_id === props.ward_id)
      .sort((a, b) => a.priority - b.priority);

    return (
      <div className="flex h-full min-h-0 flex-col">
        <WardDetailHeader
          ward={props}
          totalWards={profiles?.n_wards ?? wards.length}
          onClose={() => onSelectWard(null)}
        />
        {/* type="always": the profile is taller than the panel, and a
            hover-only scrollbar gave no cue that there was more below. */}
        <ScrollArea type="always" className="min-h-0 flex-1">
          <WardDetail
            ward={props}
            profile={profiles?.wards.find((w) => w.ward_id === props.ward_id) ?? null}
            city={profiles?.city ?? null}
            recs={wardRecs}
            totalWards={profiles?.n_wards ?? wards.length}
            onSelectWard={onSelectWard}
          />
        </ScrollArea>
      </div>
    );
  }

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
