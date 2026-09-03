"use client";

/**
 * The dashboard footer's data-vintage line (issue #124).
 *
 * Reads /api/v1/meta, which reports `generated_at` and `composite_window` from
 * the committed pipeline run log. Renders nothing until that log exists — the
 * first refresh run after this ships will commit one, and the bar appears and
 * then updates itself on every later refresh, with no redeploy logic of its
 * own (the API response is cached at the edge, so refreshes propagate within
 * the cache window).
 *
 * Rendered as a sibling of the map rather than inside it on purpose: the
 * freshness statement is meta-information about the whole dashboard, not about
 * the current ward, so it sits outside the ward-selection chrome that changes
 * as the visitor navigates.
 */

import { useEffect, useState } from "react";
import { formatCompositeWindow, formatRunDate } from "@/lib/runLog";

interface MetaResponse {
  generated_at: string | null;
  composite_window: { start: string; end: string } | null;
}

export default function DataVintageBar() {
  const [meta, setMeta] = useState<MetaResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v1/meta", { signal: controller.signal })
      .then((res) => (res.ok ? (res.json() as Promise<MetaResponse>) : null))
      .then((json) => setMeta(json))
      // A failed meta fetch must never take the dashboard down with it; the
      // bar is informational. Absence and error both just mean "no line".
      .catch(() => setMeta(null));
    return () => controller.abort();
  }, []);

  const refreshDate = formatRunDate(meta?.generated_at);
  if (!refreshDate) return null;

  const windowLabel = formatCompositeWindow(meta?.composite_window ?? null);

  return (
    <footer className="border-t border-border bg-background px-4 py-1.5">
      <p className="text-center text-[11px] text-muted-foreground sm:text-left">
        {windowLabel ? (
          <>
            Data refreshed {refreshDate} &middot; computed from imagery captured{" "}
            {windowLabel}
          </>
        ) : (
          <>Data refreshed {refreshDate}</>
        )}
      </p>
    </footer>
  );
}
