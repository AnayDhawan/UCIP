"use client";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { FACTOR_LABELS, INDICATOR_KEYS } from "@/lib/wardTypes";
import { useWardData } from "@/lib/useWardData";

export default function WardCompare({ wardIds, onClose }: { wardIds: string[]; onClose: () => void }) {
  const { wards, recs, error } = useWardData();
  const compared = wardIds
    .map((id) => wards?.find((ward) => ward.properties.ward_id === id))
    .filter((ward): ward is NonNullable<typeof ward> => Boolean(ward));

  return (
    <Dialog open={wardIds.length >= 2} onOpenChange={(open) => !open && onClose()} modal={false}>
      <DialogContent
        showOverlay={false}
        className="bottom-4 top-auto max-h-[min(72dvh,38rem)] max-w-[min(96vw,72rem)] translate-y-0"
        aria-describedby="ward-compare-description"
      >
        <DialogTitle className="px-4 pt-4 text-base">Ward comparison</DialogTitle>
        <DialogDescription id="ward-compare-description" className="px-4 pb-3">
          Comparing followed wards. This view is saved in the URL.
        </DialogDescription>
        {error && <p className="px-4 pb-4 text-sm text-destructive">Failed to load wards: {error}</p>}
        {!error && !wards && <p className="px-4 pb-4 text-sm text-muted-foreground">Loading wards…</p>}
        {compared.length >= 2 && (
          <div className="overflow-auto border-t border-border">
            <table className="w-full min-w-[36rem] text-left text-xs">
              <thead className="sticky top-0 bg-background">
                <tr className="border-b border-border">
                  <th className="p-3 font-medium text-muted-foreground">Measure</th>
                  {compared.map(({ properties }) => <th key={properties.ward_id} className="p-3 font-semibold">Ward {properties.ward_id}</th>)}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border"><th className="p-3 font-medium">HVI</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3 font-mono">{properties.HVI?.toFixed(1) ?? "n/a"}</td>)}</tr>
                <tr className="border-b border-border"><th className="p-3 font-medium">City rank</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3">{properties.rank ?? "n/a"}</td>)}</tr>
                {INDICATOR_KEYS.map((key) => (
                  <tr key={key} className="border-b border-border"><th className="p-3 font-medium">{FACTOR_LABELS[key]}</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3 font-mono">{typeof properties[`contrib_${key}`] === "number" ? (properties[`contrib_${key}`] as number).toFixed(2) : "n/a"}</td>)}</tr>
                ))}
                <tr><th className="p-3 align-top font-medium">Recommendations</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3">{(recs ?? []).filter((rec) => rec.ward_id === properties.ward_id).sort((a, b) => a.priority - b.priority).map((rec) => <p key={rec.intervention} className="mb-1">{rec.intervention}</p>) || "n/a"}</td>)}</tr>
              </tbody>
            </table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
