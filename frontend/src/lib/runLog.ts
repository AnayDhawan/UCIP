/**
 * Shared types and formatting for the pipeline run log (data/pipeline_run_log.json).
 *
 * Why this exists as a lib: the run log is what makes the site's data-age story
 * honest (issue #124). Three consumers read it — /api/v1/meta (raw values),
 * the /methodology page and the dashboard footer bar (human labels) — and they
 * must agree on its shape and on how the dates are written. A refresh date
 * alone overstates freshness, so the log also carries the dry-season window the
 * run's figures were computed from, and callers show the two as one statement.
 *
 * The file is written by pipeline/run_pipeline.py and mirrored to
 * frontend/public/ (see pipeline/README.md's "Frontend sync" table). It only
 * exists in the repo once a pipeline run has committed it, so every consumer
 * treats its absence as "no refresh has been recorded yet" and renders nothing
 * rather than a guessed date.
 */

/** ISO 8601 timestamps, written by run_pipeline.py as UTC (`...Z` or `+00:00`). */
export interface CompositeWindow {
  /** First day of the season, e.g. "2025-11-01". */
  start: string;
  /** Last day of the season, e.g. "2026-02-28". */
  end: string;
}

export interface RunStage {
  id: string;
  script: string;
  status: "ok" | "warn" | "fail" | "skipped";
  returncode: number | null;
  seconds: number;
}

export interface RunLog {
  started_at: string;
  finished_at: string | null;
  /** Present on every log this project writes going forward (issue #124). */
  composite_window: CompositeWindow | null;
  stages: RunStage[];
}

/**
 * Dates are rendered as e.g. "3 Sep 2026". Written by hand rather than
 * Intl.DateTimeFormat because the abbreviation is locale-dependent even at a
 * fixed timeZone (en-GB renders "3 Sept 2026", en-US reorders the parts to
 * "Sep 3, 2026") and this text is embedded in sentences on server- and
 * client-rendered pages that must not disagree with each other.
 */
const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
] as const;

/** Formats a UTC date as "3 Sep 2026", or null when unparseable. */
function formatUtcDate(date: Date): string | null {
  if (Number.isNaN(date.getTime())) return null;
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}

/**
 * "2026-09-03T12:40:11+00:00" -> "3 Sep 2026".
 *
 * UTC on purpose: run-log timestamps are UTC instants, and rendering them in
 * the server's or visitor's timezone would make the same refresh show as
 * different days depending on where the page was built or viewed.
 */
export function formatRunDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  return formatUtcDate(new Date(iso));
}

/** "2025-11-01" -> "1 Nov 2025". Window dates are date-only, not instants. */
export function formatWindowDate(isoDate: string | null | undefined): string | null {
  if (!isoDate) return null;
  return formatUtcDate(new Date(`${isoDate}T00:00:00Z`));
}

/**
 * {"start": "2025-11-01", "end": "2026-02-28"} -> "1 Nov 2025 – 28 Feb 2026".
 * Returns null when either bound is missing or unparseable.
 */
export function formatCompositeWindow(
  window: CompositeWindow | null | undefined
): string | null {
  if (!window) return null;
  const start = formatWindowDate(window.start);
  const end = formatWindowDate(window.end);
  if (!start || !end) return null;
  return `${start} – ${end}`;
}
