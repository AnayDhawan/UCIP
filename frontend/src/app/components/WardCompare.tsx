"use client";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { INDICATOR_KEYS } from "@/lib/wardTypes";
import { useWardData } from "@/lib/useWardData";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import { translateRec } from "@/lib/i18n";

export default function WardCompare({ wardIds, onClose }: { wardIds: string[]; onClose: () => void }) {
  const { t, f } = useLocale();
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
        <DialogTitle className="px-4 pt-4 text-base">{t.compare.heading}</DialogTitle>
        <DialogDescription id="ward-compare-description" className="px-4 pb-3">
          {t.compare.description}
        </DialogDescription>
        {error && <p className="px-4 pb-4 text-sm text-destructive">{f(t.compare.loadFailed, { error })}</p>}
        {!error && !wards && <p className="px-4 pb-4 text-sm text-muted-foreground">{t.wardList.loading}</p>}
        {compared.length >= 2 && (
          <div className="overflow-auto border-t border-border">
            <table className="w-full min-w-[36rem] text-left text-xs">
              <thead className="sticky top-0 bg-background">
                <tr className="border-b border-border">
                  <th className="p-3 font-medium text-muted-foreground">{t.compare.measure}</th>
                  {compared.map(({ properties }) => <th key={properties.ward_id} className="p-3 font-semibold">{f(t.ward.label, { ward: properties.ward_id })}</th>)}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border"><th className="p-3 font-medium">{t.compare.hvi}</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3 font-mono">{properties.HVI?.toFixed(1) ?? t.compare.notAvailable}</td>)}</tr>
                <tr className="border-b border-border"><th className="p-3 font-medium">{t.compare.cityRank}</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3">{properties.rank ?? t.compare.notAvailable}</td>)}</tr>
                {INDICATOR_KEYS.map((key) => (
                  <tr key={key} className="border-b border-border"><th className="p-3 font-medium">{t.ward.factors[key]}</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3 font-mono">{typeof properties[`contrib_${key}`] === "number" ? (properties[`contrib_${key}`] as number).toFixed(2) : t.compare.notAvailable}</td>)}</tr>
                ))}
                <tr><th className="p-3 align-top font-medium">{t.compare.recommendations}</th>{compared.map(({ properties }) => <td key={properties.ward_id} className="p-3">{(recs ?? []).filter((rec) => rec.ward_id === properties.ward_id).sort((a, b) => a.priority - b.priority).map((rec) => <p key={rec.intervention} className="mb-1">{translateRec(t, "interventions", rec.intervention)}</p>) || t.compare.notAvailable}</td>)}</tr>
              </tbody>
            </table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
