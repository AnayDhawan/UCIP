"use client";

import { useMemo, useState } from "react";
import { Check, Search, Star, Link2 } from "lucide-react";
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
  trackedWards = [],
  onToggleTracked,
}: {
  selectedWardId: string | null;
  onSelectWard: (wardId: string | null) => void;
  /** Ward ids the visitor is following, from the `wards` URL param. */
  trackedWards?: string[];
  onToggleTracked?: (wardId: string) => void;
}) {
  const { wards, recs, profiles, error } = useWardData();
  const [search, setSearch] = useState("");
  const [copied, setCopied] = useState(false);

  async function copyTrackedLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied outright; the URL is in the address bar
      // either way, so there is nothing useful to tell the user here.
    }
  }

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

  /**
   * Followed wards float to the top, each group still ranked most vulnerable
   * first. Sorting rather than splitting into two lists keeps one scroll
   * container and one set of rank numbers, so a followed ward still shows its
   * real city-wide rank rather than its position in a shortlist.
   */
  const ordered = useMemo(() => {
    if (trackedWards.length === 0) return filtered;
    const isTracked = (id: string) => trackedWards.includes(id);
    return [...filtered].sort((a, b) => {
      const at = isTracked(a.properties.ward_id) ? 0 : 1;
      const bt = isTracked(b.properties.ward_id) ? 0 : 1;
      if (at !== bt) return at - bt;
      return (a.properties.rank ?? 99) - (b.properties.rank ?? 99);
    });
  }, [filtered, trackedWards]);

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
        {/* Native scroller (see .ward-scroll in globals.css): the profile runs
            taller than the panel and needs an unambiguous, always-present
            scrollbar rather than an overlay one. */}
        <div className="ward-scroll min-h-0 flex-1 overflow-y-auto">
          <WardDetail
            ward={props}
            profile={profiles?.wards.find((w) => w.ward_id === props.ward_id) ?? null}
            city={profiles?.city ?? null}
            recs={wardRecs}
            totalWards={profiles?.n_wards ?? wards.length}
            onSelectWard={onSelectWard}
          />
        </div>
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
      {trackedWards.length > 0 && (
        <div className="flex items-center justify-between gap-2 border-b border-border bg-accent/40 px-4 py-2">
          <p className="min-w-0 truncate text-xs text-muted-foreground">
            Following{" "}
            <span className="font-medium text-foreground">
              {trackedWards.length} ward{trackedWards.length === 1 ? "" : "s"}
            </span>
          </p>
          <button
            onClick={copyTrackedLink}
            className="flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            {copied ? <Check className="h-3 w-3" aria-hidden /> : <Link2 className="h-3 w-3" aria-hidden />}
            {copied ? "Copied" : "Copy link"}
          </button>
        </div>
      )}
      <ScrollArea className="min-h-0 flex-1">
        <div className="divide-y divide-border">
          {ordered.map((f) => {
            const p = f.properties;
            // Selection no longer swaps this panel's view, so the row itself has
            // to show which ward the map and dialog are on.
            const isSelected = p.ward_id === selectedWardId;
            const isTracked = trackedWards.includes(p.ward_id);
            return (
              <div
                key={p.ward_id}
                className={`flex w-full items-center gap-1 transition-colors hover:bg-accent ${
                  isSelected ? "bg-accent" : ""
                }`}
              >
                <button
                  onClick={() => onSelectWard(p.ward_id)}
                  title={areasForWard(p.ward_id).join(", ")}
                  aria-current={isSelected ? "true" : undefined}
                  className="flex min-w-0 flex-1 items-center justify-between gap-3 py-2.5 pl-4 text-left"
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
                {onToggleTracked && (
                  <button
                    onClick={() => onToggleTracked(p.ward_id)}
                    aria-pressed={isTracked}
                    aria-label={
                      isTracked ? `Stop following ward ${p.ward_id}` : `Follow ward ${p.ward_id}`
                    }
                    title={isTracked ? "Stop following" : "Follow this ward"}
                    className="mr-2 shrink-0 rounded p-1.5 text-muted-foreground transition-colors hover:bg-background hover:text-foreground"
                  >
                    <Star
                      className={`h-3.5 w-3.5 ${isTracked ? "fill-brand-teal text-brand-teal" : ""}`}
                      aria-hidden
                    />
                  </button>
                )}
              </div>
            );
          })}
          {ordered.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No ward matches &quot;{search}&quot;.</p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
