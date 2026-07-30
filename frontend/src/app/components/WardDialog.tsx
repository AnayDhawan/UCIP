"use client";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import WardDetail from "./WardDetail";
import WardDetailHeader from "./WardDetailHeader";
import { useWardData } from "@/lib/useWardData";

/**
 * The ward profile for the two cases with no sidebar to hand over: fullscreen,
 * which unmounts the aside, and viewports below `md`, where the aside is
 * hidden. Everywhere else WardPanel shows the same content in place.
 *
 * Open state is derived from the URL's `?ward=` param, which dashboard/page.tsx
 * owns, so there is no second source of truth for selection and browser Back
 * still steps through selections.
 */
export default function WardDialog({
  selectedWardId,
  onSelectWard,
  enabled,
}: {
  selectedWardId: string | null;
  onSelectWard: (wardId: string | null) => void;
  /** False whenever the sidebar is showing the ward instead. */
  enabled: boolean;
}) {
  const { wards, recs, profiles, error } = useWardData();

  const selected = wards?.find((f) => f.properties.ward_id === selectedWardId) ?? null;
  const props = selected?.properties;
  const wardRecs = selectedWardId
    ? (recs ?? [])
        .filter((r) => r.ward_id === selectedWardId)
        .sort((a, b) => a.priority - b.priority)
    : [];
  const totalWards = profiles?.n_wards ?? wards?.length ?? 24;

  return (
    <Dialog
      open={enabled && Boolean(selectedWardId)}
      onOpenChange={(open: boolean) => {
        if (!open) onSelectWard(null);
      }}
    >
      <DialogContent
        aria-describedby={undefined}
        aria-labelledby="ward-dialog-title"
        showCloseButton={false}
        className="max-w-md"
      >
        {props ? (
          <WardDetailHeader
            ward={props}
            totalWards={totalWards}
            onClose={() => onSelectWard(null)}
            titleId="ward-dialog-title"
          />
        ) : (
          <DialogTitle id="ward-dialog-title" className="px-4 py-3">
            Ward {selectedWardId}
          </DialogTitle>
        )}

        <div className="ward-scroll min-h-0 flex-1 overflow-y-auto">
          {error && (
            <p className="px-4 py-4 text-sm text-destructive">Failed to load ward data: {error}</p>
          )}
          {!error && !props && (
            <p className="px-4 py-4 text-sm text-muted-foreground">Loading ward…</p>
          )}
          {props && (
            <WardDetail
              ward={props}
              profile={profiles?.wards.find((w) => w.ward_id === props.ward_id) ?? null}
              city={profiles?.city ?? null}
              recs={wardRecs}
              totalWards={totalWards}
              onSelectWard={onSelectWard}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
