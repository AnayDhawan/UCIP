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

export type DailyForecast = {
  /** Local calendar date, YYYY-MM-DD, in the timezone the request asked for. */
  date: string;
  maxC: number;
  minC: number;
  /** Null when Open-Meteo has no precipitation probability for that day. */
  rainChancePct: number | null;
};

export type PointForecast = {
  temperatureC: number;
  /** "Feels like" air temperature. */
  apparentC: number;
  observedAt: string;
  /** Seven days, today first. */
  days: DailyForecast[];
};

/**
 * Current conditions and a 7-day forecast for one point, from Open-Meteo.
 * This is Open-Meteo's forecast, not UCIP's: the heat vulnerability score is
 * not a forecast, and the ward weather panel labels the source.
 *
 * Same rule as fetchCityTemp: null on any failure or malformed body, never a
 * fallback or invented number. This function does not cache; a caller that does
 * should show `observedAt` so the reading's age is visible.
 */
export async function fetchPointForecast(
  lat: number,
  lon: number,
  timezone: string
): Promise<PointForecast | null> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const url = new URL("https://api.open-meteo.com/v1/forecast");
    url.searchParams.set("latitude", String(lat));
    url.searchParams.set("longitude", String(lon));
    url.searchParams.set("current", "temperature_2m,apparent_temperature");
    url.searchParams.set(
      "daily",
      "temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    );
    url.searchParams.set("forecast_days", "7");
    url.searchParams.set("timezone", timezone);

    const res = await fetch(url.toString(), { signal: controller.signal });
    if (!res.ok) return null;

    const data = (await res.json()) as {
      current?: { temperature_2m?: unknown; apparent_temperature?: unknown; time?: string };
      daily?: {
        time?: unknown[];
        temperature_2m_max?: unknown[];
        temperature_2m_min?: unknown[];
        precipitation_probability_max?: unknown[];
      };
    };
    const temperatureC = data.current?.temperature_2m;
    const apparentC = data.current?.apparent_temperature;
    const daily = data.daily;
    if (typeof temperatureC !== "number" || typeof apparentC !== "number" || !daily?.time) {
      return null;
    }

    const days: DailyForecast[] = [];
    for (const [i, date] of daily.time.entries()) {
      const maxC = daily.temperature_2m_max?.[i];
      const minC = daily.temperature_2m_min?.[i];
      const rain = daily.precipitation_probability_max?.[i];
      if (typeof date !== "string" || typeof maxC !== "number" || typeof minC !== "number") {
        return null;
      }
      days.push({ date, maxC, minC, rainChancePct: typeof rain === "number" ? rain : null });
    }
    if (days.length === 0) return null;

    return { temperatureC, apparentC, observedAt: data.current?.time ?? "", days };
  } catch (err) {
    console.error("[weather] fetchPointForecast failed:", err);
    return null;
  } finally {
    clearTimeout(timeout);
  }
}
