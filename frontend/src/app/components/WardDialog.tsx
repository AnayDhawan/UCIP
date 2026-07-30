"use client";

import { useEffect, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import WardDetail from "./WardDetail";
import { hviColor } from "@/lib/hvi";
import type { NbsRec, WardProps } from "@/lib/wardTypes";
import { WARD_PROFILES_URL, type WardProfileData } from "@/lib/wardProfile";

/**
 * The dashboard's single ward surface.
 *
 * Open state is derived straight from the URL's `?ward=` param, which
 * dashboard/page.tsx owns, so there is no second source of truth for selection
 * and browser Back still steps through selections. Closing simply clears it.
 *
 * This replaces both the old sidebar detail view and the fullscreen-only
 * Leaflet popup. Those two only ever covered a desktop, non-fullscreen window
 * between them: the sidebar is `hidden md:block` and is unmounted in
 * fullscreen, which left phones and fullscreen with no way to read a ward.
 */
export default function WardDialog({
  selectedWardId,
  onSelectWard,
  compact = false,
}: {
  selectedWardId: string | null;
  onSelectWard: (wardId: string | null) => void;
  /** Outside fullscreen the map is already boxed in by the header and the ward
   *  list, so a large dialog swallows the whole view. In fullscreen there is
   *  room to spare, so it opens wider and taller. */
  compact?: boolean;
}) {
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
        setWards(wardsData.features);
        setRecs(recsData);
      })
      .catch((err) => {
        if (!cancelled) setError(String(err));
      });

    // The descriptive profile is additive: without it the dialog still shows
    // the score, the breakdown and the interventions, so a failure here must
    // not block the rest.
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

  const selected = wards?.find((f) => f.properties.ward_id === selectedWardId) ?? null;
  const profile = profiles?.wards.find((w) => w.ward_id === selectedWardId) ?? null;
  const wardRecs = selectedWardId
    ? (recs ?? []).filter((r) => r.ward_id === selectedWardId).sort((a, b) => a.priority - b.priority)
    : [];

  const props = selected?.properties;

  return (
    <Dialog
      open={Boolean(selectedWardId)}
      onOpenChange={(open: boolean) => {
        if (!open) onSelectWard(null);
      }}
    >
      <DialogContent
        aria-describedby={undefined}
        className={compact ? "max-w-sm max-h-[min(70dvh,100dvh-2rem)] text-[13px]" : undefined}
      >
        <DialogHeader>
          <div className="flex items-center gap-2">
            {props && (
              <Badge
                className="h-7 w-7 justify-center rounded-full p-0 text-xs font-semibold text-black/80"
                style={{ background: hviColor(props.HVI) }}
              >
                {props.rank}
              </Badge>
            )}
            <DialogTitle>Ward {selectedWardId}</DialogTitle>
            {props?.HVI !== null && props?.HVI !== undefined && (
              <span className="ml-auto font-mono text-sm text-muted-foreground">
                HVI {props.HVI.toFixed(1)}
              </span>
            )}
          </div>
          {props && (
            <DialogDescription className="mt-1">
              Priority {props.rank} of {wards?.length ?? 24} &middot; {props.n_cells ?? "n/a"} grid
              cells
            </DialogDescription>
          )}
        </DialogHeader>

        <ScrollArea className="min-h-0 flex-1">
          {error && <p className="px-6 py-5 text-sm text-destructive">Failed to load ward data: {error}</p>}
          {!error && !props && (
            <p className="px-6 py-5 text-sm text-muted-foreground">Loading ward…</p>
          )}
          {props && (
            <WardDetail
              ward={props}
              profile={profile}
              city={profiles?.city ?? null}
              recs={wardRecs}
              totalWards={profiles?.n_wards ?? wards?.length ?? 24}
              onSelectWard={onSelectWard}
            />
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
