/**
 * GET /api/weather/{wardSlug}
 *
 * Open-Meteo current conditions and 7-day forecast at the ward's centroid, for
 * the ward weather panel. This is Open-Meteo's forecast, not UCIP's. It lives
 * outside /api/v1 because it is not part of the public data contract.
 *
 * A success is cacheable for 30 minutes (s-maxage, the same mechanism as the v1
 * API), so 24 wards cost Open-Meteo a few dozen requests an hour however many
 * people open them. `revalidate` alone does not cache a route with a dynamic
 * segment. Failures carry no cache header and return an error with no numbers.
 */

import { ACTIVE_CITY } from "@/lib/city";
import { centroidOf } from "@/lib/geometry";
import { fetchPointForecast } from "@/lib/weather";
import { wardFromSlug } from "@/lib/wardSnapshot";

export const revalidate = 1800;

const CACHE_HEADER = "public, s-maxage=1800, stale-while-revalidate=3600";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ wardId: string }> }
) {
  const { wardId } = await params;
  const ward = wardFromSlug(wardId);
  if (!ward) return Response.json({ error: `No ward '${wardId}'.` }, { status: 404 });

  const centroid = centroidOf(ward.geometry);
  const forecast = centroid && (await fetchPointForecast(centroid[0], centroid[1], ACTIVE_CITY.timezone));
  if (!forecast) return Response.json({ error: "Weather is unavailable right now." }, { status: 502 });

  return Response.json(forecast, { headers: { "cache-control": CACHE_HEADER } });
}
