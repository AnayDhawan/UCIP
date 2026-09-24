"use client";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import WardDetail from "./WardDetail";
import WardDetailHeader from "./WardDetailHeader";
import WardStaticMap from "./WardStaticMap";
import WardTrend from "./WardTrend";
import { useWardData } from "@/lib/useWardData";
import { useLocale } from "@/lib/i18n/LocaleProvider";

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
  const { t, f } = useLocale();
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
        aria-describedby="ward-dialog-description"
        aria-labelledby="ward-dialog-title"
        showCloseButton={false}
        className="max-w-md"
      >
        <DialogDescription id="ward-dialog-description" className="sr-only">
          {t.ward.dialogDescription}
        </DialogDescription>
        {props ? (
          <WardDetailHeader
            ward={props}
            totalWards={totalWards}
            onClose={() => onSelectWard(null)}
            titleId="ward-dialog-title"
          />
        ) : (
          <DialogTitle id="ward-dialog-title" className="px-4 py-3">
            {f(t.ward.label, { ward: selectedWardId ?? "" })}
          </DialogTitle>
        )}

        <div className="ward-scroll min-h-0 flex-1 overflow-y-auto">
          {error && (
            <p className="px-4 py-4 text-sm text-destructive">{f(t.ward.loadFailed, { error })}</p>
          )}
          {!error && !props && (
            <p className="px-4 py-4 text-sm text-muted-foreground">{t.ward.loading}</p>
          )}
          {props && (
            <>
              {selected.geometry && <WardStaticMap geometry={selected.geometry} hvi={props.HVI} label={f(t.ward.label, { ward: props.ward_id })} />}
              <WardDetail
                ward={props}
                profile={profiles?.wards.find((w) => w.ward_id === props.ward_id) ?? null}
                city={profiles?.city ?? null}
                recs={wardRecs}
                totalWards={totalWards}
                onSelectWard={onSelectWard}
              />
              {/* Multi-year trend (issue #89). Renders nothing when the time
                  series is absent, so a checkout without a stage 14 run shows
                  the dialog exactly as before. */}
              <div className="px-4 pb-4">
                <WardTrend wardId={props.ward_id} />
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
