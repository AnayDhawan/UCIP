/**
 * Live current air temperature for the configured city, via Open-Meteo
 * (api.open-meteo.com) — free, no API key, no rate-limit auth. Used by
 * `LiveTempStrip` to give a real, live number to contrast against the map's
 * land-surface-temperature proxy.
 *
 * Deliberately returns `null` on any failure rather than a stale or fabricated
 * value: UCIP's own product rule is "numbers are real, never invented," and a
 * live-weather widget has no honest static-snapshot fallback the way the map's
 * satellite data does.
 */

import type { CityConfig } from "./city";

const FETCH_TIMEOUT_MS = 5000;

export type CityTemp = {
  temperatureC: number;
  observedAt: string;
};

export async function fetchCityTemp(city: CityConfig): Promise<CityTemp | null> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const url = new URL("https://api.open-meteo.com/v1/forecast");
    url.searchParams.set("latitude", String(city.lat));
    url.searchParams.set("longitude", String(city.lon));
    url.searchParams.set("current", "temperature_2m");
    url.searchParams.set("timezone", city.timezone);

    const res = await fetch(url.toString(), { signal: controller.signal });
    if (!res.ok) return null;

    const data = (await res.json()) as {
      current?: { temperature_2m?: number; time?: string };
    };
    const temperatureC = data.current?.temperature_2m;
    if (typeof temperatureC !== "number") return null;

    return { temperatureC, observedAt: data.current?.time ?? "" };
  } catch (err) {
    console.error("[weather] fetchCityTemp failed:", err);
    return null;
  } finally {
    clearTimeout(timeout);
  }
}
