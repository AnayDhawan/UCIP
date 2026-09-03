/**
 * Tracked wards, kept in the URL rather than behind an account.
 *
 * Issues #59, #60 and #62 proposed Supabase Auth, a profiles table with a
 * saved_wards column, and Resend email digests, to let someone follow the wards
 * they care about. That is a login wall, a user table, an email integration and
 * a permanent maintenance surface, added to a public data tool that has no users
 * asking for it and stores nothing private.
 *
 * The URL does the same job. `/dashboard?wards=F/N,G/S` IS the saved set: it
 * survives a reload, syncs across devices by being pasted, works with no
 * account, can be bookmarked, and can be sent to a colleague, which an account
 * cannot. localStorage carries it between visits on one device so the set is not
 * lost by navigating away, but the URL always wins when it carries a set, so a
 * shared link shows the sender's wards and not the recipient's.
 *
 * The one thing this genuinely cannot do is push a notification when a ward's
 * score changes. That is real, and it is the thing to revisit if anyone ever
 * asks for it; the pipeline already computes the change (pipeline/diff_snapshots.py),
 * so the missing piece would be a delivery channel, not the detection.
 */

const STORAGE_KEY = "ucip-tracked-wards";

/** Cap on how many wards a link may carry. There are only 24. */
const MAX_TRACKED = 24;

/**
 * Ward ids are BMC codes: one or two uppercase letters, optionally with a
 * single-letter suffix after a slash (A, L, F/N, R/C). Anything else in the URL
 * is discarded rather than trusted, since these values reach React keys, map
 * lookups and the document title.
 */
const WARD_ID_PATTERN = /^[A-Z]{1,2}(\/[A-Z])?$/;

export function parseWardParam(raw: string | null): string[] {
  if (!raw) return [];
  const seen = new Set<string>();
  for (const part of raw.split(",")) {
    const id = part.trim().toUpperCase();
    if (WARD_ID_PATTERN.test(id)) seen.add(id);
    if (seen.size >= MAX_TRACKED) break;
  }
  return [...seen];
}

export function serializeWardParam(wardIds: string[]): string {
  return wardIds.join(",");
}

export function toggleWard(wardIds: string[], wardId: string): string[] {
  return wardIds.includes(wardId)
    ? wardIds.filter((id) => id !== wardId)
    : [...wardIds, wardId];
}

/**
 * Reads the remembered set. Wrapped because localStorage throws outright in
 * some privacy modes rather than returning null, and a dashboard that cannot
 * render because someone blocked site data would be a bad trade for a
 * convenience feature.
 */
export function readStoredWards(): string[] {
  try {
    return parseWardParam(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return [];
  }
}

export function writeStoredWards(wardIds: string[]): void {
  try {
    if (wardIds.length === 0) window.localStorage.removeItem(STORAGE_KEY);
    else window.localStorage.setItem(STORAGE_KEY, serializeWardParam(wardIds));
  } catch {
    // Ignored: tracking wards is a convenience, not a guarantee.
  }
}
