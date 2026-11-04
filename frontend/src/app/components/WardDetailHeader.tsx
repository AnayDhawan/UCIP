"use client";

import { Check, Code2, Link2, MessageCircle, Printer, Share2, X } from "lucide-react";
import { useState, useSyncExternalStore } from "react";
import { Badge } from "@/components/ui/badge";
import { hviColor } from "@/lib/hvi";
import { FACTOR_LABELS, INDICATOR_KEYS, type WardProps } from "@/lib/wardTypes";
import { intervalWidth, rankRangeLabel, type WardInterval } from "@/lib/rankUncertainty";
import { wardSlug } from "@/lib/wardSlug";
import { wardPageUrl, wardShareText, whatsappHref } from "@/lib/wardShare";

const ACTION =
  "shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground print:hidden";

// navigator.share exists on phones and some desktops; false while rendering on the server.
const noopSubscribe = () => () => {};
const canNativeShare = () => typeof navigator.share === "function";

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
  interval,
}: {
  ward: WardProps;
  totalWards: number;
  onClose: () => void;
  /** Set when the header's title doubles as a dialog's accessible name. */
  titleId?: string;
  /** The ward's 95% rank interval, when the uncertainty file has one (issue #169). */
  interval?: WardInterval;
}) {
  const [copied, setCopied] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const nativeShare = useSyncExternalStore(noopSubscribe, canNativeShare, () => false);
  const pageUrl = wardPageUrl(ward.ward_id);
  const shareText = wardShareText(ward.ward_id, ward.rank, totalWards);

  async function copyEmbed() {
    const src = `${window.location.origin}/embed/ward/${wardSlug(ward.ward_id)}`;
    try {
      await navigator.clipboard.writeText(`<iframe src="${src}" title="UCIP Ward ${ward.ward_id}" width="100%" height="250" loading="lazy"></iframe>`);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // The URL remains directly accessible when clipboard permission is denied.
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(pageUrl);
      setLinkCopied(true);
      window.setTimeout(() => setLinkCopied(false), 2000);
    } catch {
      // The page stays reachable from the WhatsApp link when clipboard permission is denied.
    }
  }

  async function shareNatively() {
    try {
      await navigator.share({ title: `UCIP ward ${ward.ward_id}`, text: shareText, url: pageUrl });
    } catch {
      // Closing the share sheet rejects; nothing to report.
    }
  }

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
          onClick={copyEmbed}
          aria-label={`Copy embed code for ward ${ward.ward_id}`}
          title="Copy embed code"
          className={ACTION}
        >
          {copied ? <Check className="h-4 w-4" /> : <Code2 className="h-4 w-4" />}
        </button>
        <button
          onClick={() => window.print()}
          aria-label={`Print ward ${ward.ward_id} brief`}
          title="Print ward brief"
          className={ACTION}
        >
          <Printer className="h-4 w-4" />
        </button>
        <button
          onClick={onClose}
          aria-label="Close ward details"
          className="-mr-1 shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring print:hidden"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      {/* Share actions sit on this row because the identity row above is already full. */}
      <div className="mt-1 flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          Priority {ward.rank} of {totalWards} &middot; {ward.n_cells ?? "n/a"} grid cells
        </p>
        <div className="-my-1 flex shrink-0 items-center gap-1">
          <a
            href={whatsappHref(shareText, pageUrl)}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Share ward ${ward.ward_id} on WhatsApp`}
            title="Share on WhatsApp"
            className={ACTION}
          >
            <MessageCircle className="h-4 w-4" />
          </a>
          <button
            onClick={copyLink}
            aria-label={`Copy link to ward ${ward.ward_id} page`}
            title="Copy link"
            className={ACTION}
          >
            {linkCopied ? <Check className="h-4 w-4" /> : <Link2 className="h-4 w-4" />}
          </button>
          {nativeShare && (
            <button
              onClick={shareNatively}
              aria-label={`Share ward ${ward.ward_id}`}
              title="Share"
              className={ACTION}
            >
              <Share2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      {interval && (
        <p className="mt-1 text-xs text-muted-foreground">
          Rank is uncertain: likely {rankRangeLabel(interval)} (95% range, {intervalWidth(interval)} places
          wide). Based on sampling of grid cells only.
        </p>
      )}
      {ward.single_factor_dominated && ward.dominant_factor && (
        <p className="mt-1 text-xs text-muted-foreground">
          Mostly driven by one measure:{" "}
          {FACTOR_LABELS[ward.dominant_factor as (typeof INDICATOR_KEYS)[number]] ?? ward.dominant_factor}
          {typeof ward.dominant_share === "number"
            ? ` (${Math.round(ward.dominant_share * 100)}% of the score's movement)`
            : ""}
          .
        </p>
      )}
    </div>
  );
}
