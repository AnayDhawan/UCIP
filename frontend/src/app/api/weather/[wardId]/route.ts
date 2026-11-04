/**
 * GET /api/weather/{wardSlug}
 *
 * Open-Meteo current conditions and 7-day forecast at the ward's centroid, for
 * the ward weather panel. This is Open-Meteo's forecast, not UCIP's. It lives
 * outside /api/v1 because it is not part of the public data contract.
 *
 * A success is cacheable at the CDN for 30 minutes (s-maxage, the same mechanism
 * as the v1 API), so the panel shows the reading time from `observedAt`. A
 * failure is cached for 30 seconds so an outage does not make every panel open
 * wait out the upstream timeout. Both return no numbers on failure.
 *
 * Rate limited per client like the v1 API: a loop that varies the query string
 * would otherwise miss the CDN cache and spend UCIP's Open-Meteo quota.
 */

import { ACTIVE_CITY } from "@/lib/city";
import { centroidOf } from "@/lib/geometry";
import { checkRateLimit } from "@/lib/rateLimit";
import { fetchPointForecast } from "@/lib/weather";
import { wardFromSlug } from "@/lib/wardSnapshot";

const CACHE_HEADER = "public, s-maxage=1800, stale-while-revalidate=600";
const ERROR_CACHE_HEADER = "public, s-maxage=30";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ wardId: string }> }
) {
  const limit = await checkRateLimit(request.headers);
  if (limit && !limit.ok) {
    return Response.json(
      { error: "Too many requests." },
      {
        status: 429,
        headers: { "cache-control": "no-store", "retry-after": String(limit.retryAfterSeconds) },
      }
    );
  }

  const { wardId } = await params;
  const ward = wardFromSlug(wardId);
  if (!ward) return Response.json({ error: `No ward '${wardId}'.` }, { status: 404 });

  const centroid = centroidOf(ward.geometry);
  const forecast = centroid && (await fetchPointForecast(centroid[0], centroid[1], ACTIVE_CITY.timezone));
  if (!forecast) {
    return Response.json(
      { error: "Weather is unavailable right now." },
      { status: 502, headers: { "cache-control": ERROR_CACHE_HEADER } }
    );
  }

  return Response.json(forecast, { headers: { "cache-control": CACHE_HEADER } });
}
