"use client";

import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { hviColor } from "@/lib/hvi";
import type { WardProps } from "@/lib/wardTypes";

/**
 * The identity strip at the top of a ward surface: rank badge, ward code, HVI,
 * and the priority line, with a close control on the right.
 *
 * Shared so the sidebar detail view and the fullscreen/mobile dialog present a
 * selected ward identically; only their containers differ.
 */
export default function WardDetailHeader({
  ward,
  totalWards,
  onClose,
  titleId,
}: {
  ward: WardProps;
  totalWards: number;
  onClose: () => void;
  /** Set when the header's title doubles as a dialog's accessible name. */
  titleId?: string;
}) {
  return (
    <div className="shrink-0 border-b border-border px-4 py-3">
      <div className="flex items-center gap-2">
        <Badge
          className="h-7 w-7 shrink-0 justify-center rounded-full p-0 text-xs font-semibold text-black/80"
          style={{ background: hviColor(ward.HVI) }}
        >
          {ward.rank}
        </Badge>
        <span id={titleId} className="text-base font-semibold text-foreground">
          Ward {ward.ward_id}
        </span>
        {ward.HVI !== null && (
          <span className="ml-auto font-mono text-sm text-muted-foreground">
            HVI {ward.HVI.toFixed(1)}
          </span>
        )}
        <button
          onClick={onClose}
          aria-label="Close ward details"
          className="-mr-1 shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Priority {ward.rank} of {totalWards} &middot; {ward.n_cells ?? "n/a"} grid cells
      </p>
    </div>
  );
}
