/**
 * Per-IP rate limiting for the public API (issue #101).
 *
 * The API is unauthenticated by design, read-only, and sits on free-tier
 * Vercel and Supabase. Without a ceiling one careless loop exhausts the quota
 * for everyone, and the dashboard goes down with it, because they share a
 * backend.
 *
 * Cache headers do most of the work. Every route carries a one-hour s-maxage
 * with a day of stale-while-revalidate, so repeated requests for the same thing
 * are served at the edge and never reach this code at all. The limiter is for
 * the traffic that defeats caching: a crawler walking every ward, or a script
 * varying a query parameter in a loop.
 *
 * Ships disabled. With no Upstash credentials configured, every request passes.
 * That is the same pattern tourneyradar-api uses, and it is what lets the code
 * land and be reviewed before the store exists, rather than a half-configured
 * limiter rejecting real traffic.
 */

import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

/**
 * 120 requests a minute per client.
 *
 * Above anything a human browsing the dashboard produces, and above a
 * reasonable script pulling the 24 wards one at a time. A consumer who wants
 * the whole dataset should be calling /export once, which this deliberately
 * leaves room for.
 */
const REQUESTS_PER_MINUTE = 120;

let limiter: Ratelimit | null | undefined;

function getLimiter(): Ratelimit | null {
  if (limiter !== undefined) return limiter;

  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;

  // No credentials means no limiting, not a crash.
  if (!url || !token) {
    limiter = null;
    return limiter;
  }

  limiter = new Ratelimit({
    redis: new Redis({ url, token }),
    limiter: Ratelimit.slidingWindow(REQUESTS_PER_MINUTE, "1 m"),
    analytics: false,
    prefix: "ucip-api",
  });
  return limiter;
}

/** Strips brackets, a port and a zone id, leaving a bare address. */
function bareAddress(raw: string): string {
  let addr = raw.trim();

  if (addr.startsWith("[")) {
    const close = addr.indexOf("]");
    if (close > 0) return addr.slice(1, close).split("%")[0];
  }

  // A single colon with a dot means IPv4 with a port; IPv6 always has two or more.
  const firstColon = addr.indexOf(":");
  if (firstColon > 0 && addr.indexOf(":", firstColon + 1) === -1 && addr.includes(".")) {
    addr = addr.slice(0, firstColon);
  }

  return addr.split("%")[0];
}

/** The eight hextets of an IPv6 address, or null if it does not parse. */
function expandIpv6(addr: string): number[] | null {
  const halves = addr.split("::");
  if (halves.length > 2) return null;

  const toHextets = (part: string): number[] | null => {
    if (part === "") return [];
    const groups = part.split(":");
    const out: number[] = [];

    for (let i = 0; i < groups.length; i++) {
      const g = groups[i];
      // A trailing dotted quad (::ffff:203.0.113.4) occupies two hextets.
      if (g.includes(".")) {
        if (i !== groups.length - 1) return null;
        const octets = g.split(".");
        if (octets.length !== 4) return null;
        const nums = octets.map((o) => (/^\d{1,3}$/.test(o) ? Number(o) : NaN));
        if (nums.some((n) => Number.isNaN(n) || n > 255)) return null;
        out.push((nums[0] << 8) | nums[1], (nums[2] << 8) | nums[3]);
        continue;
      }
      if (!/^[0-9a-fA-F]{1,4}$/.test(g)) return null;
      out.push(parseInt(g, 16));
    }
    return out;
  };

  const head = toHextets(halves[0]);
  const tail = halves.length === 2 ? toHextets(halves[1]) : [];
  if (head === null || tail === null) return null;

  if (halves.length === 1) return head.length === 8 ? head : null;

  const gap = 8 - head.length - tail.length;
  if (gap < 1) return null;
  return [...head, ...Array(gap).fill(0), ...tail];
}

/**
 * The key a request is counted against.
 *
 * IPv6 clients are keyed on their /64 rather than their full address. An ISP
 * hands a residential line a whole /64 and the client can pick any address
 * inside it per request, so keying on the full address means the same real
 * client lands in a fresh bucket every time and the limit never binds. This is
 * the same bug tourneyradar-api had, found and fixed there first.
 *
 * An address that does not parse keys on itself rather than on a shared
 * fallback, so a malformed header cannot drop unrelated callers into one
 * bucket and rate-limit them collectively.
 */
export function rateLimitKey(headers: Headers): string {
  const forwardedFor = headers.get("x-forwarded-for");
  const raw = forwardedFor
    ? forwardedFor.split(",")[0].trim()
    : headers.get("x-real-ip") ?? "unknown";

  if (raw === "unknown" || !raw.includes(":")) return raw;

  const addr = bareAddress(raw);
  if (!addr.includes(":")) return addr;

  const hextets = expandIpv6(addr);
  if (!hextets) return raw;

  // ::ffff:203.0.113.4 is an IPv4 client behind an IPv6-aware proxy. It has no
  // meaningful /64, so it keys on the IPv4 address.
  const isIpv4Mapped = hextets.slice(0, 5).every((h) => h === 0) && hextets[5] === 0xffff;
  if (isIpv4Mapped) {
    const a = hextets[6];
    const b = hextets[7];
    return `${a >> 8}.${a & 0xff}.${b >> 8}.${b & 0xff}`;
  }

  const prefix = hextets
    .slice(0, 4)
    .map((h) => h.toString(16))
    .join(":");
  return `${prefix}::/64`;
}

export type RateLimitResult = {
  ok: boolean;
  limit: number;
  remaining: number;
  retryAfterSeconds: number;
};

/**
 * Checks a request against the limit.
 *
 * Fails open. A store outage should not take down a read-only public API: the
 * worst case of letting requests through is the quota pressure that existed
 * before this file, and the worst case of failing closed is a total outage
 * caused by the thing meant to prevent one.
 */
export async function checkRateLimit(headers: Headers): Promise<RateLimitResult | null> {
  const ratelimit = getLimiter();
  if (!ratelimit) return null;

  try {
    const { success, limit, remaining, reset } = await ratelimit.limit(rateLimitKey(headers));
    return {
      ok: success,
      limit,
      remaining,
      retryAfterSeconds: Math.max(0, Math.ceil((reset - Date.now()) / 1000)),
    };
  } catch (error) {
    console.error("Rate limit check failed, failing open:", error);
    return null;
  }
}

/** Test seam: forces the limiter to be rebuilt after env vars change. */
export function _resetRateLimitForTests() {
  limiter = undefined;
}
