"use client";

import { useEffect, useState } from "react";
import { ACTIVE_CITY } from "@/lib/city";
import type { PointForecast } from "@/lib/weather";
import { wardSlug } from "@/lib/wardSlug";

/** Shown in every state, so the weather is never read as UCIP's own forecast. */
export const WEATHER_LABEL = "Forecast by Open-Meteo. UCIP's heat score is not a forecast.";

/** Three-letter weekday for a YYYY-MM-DD date, read in UTC so it cannot shift with the viewer's zone. */
function weekday(date: string): string {
  return new Date(`${date}T00:00:00Z`).toLocaleDateString("en-GB", { weekday: "short", timeZone: "UTC" });
}

/**
 * Current weather and a 7-day max/min row for one ward, from /api/weather,
 * which proxies Open-Meteo. Loading and failure are plain text: no number is
 * shown unless Open-Meteo returned it.
 */
export default function WardWeather({ wardId }: { wardId: string }) {
  const slug = wardSlug(wardId);
  const [result, setResult] = useState<{ slug: string; forecast: PointForecast | null } | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/weather/${slug}`)
      .then((res) => (res.ok ? (res.json() as Promise<PointForecast>) : null))
      .catch(() => null)
      .then((forecast) => {
        if (!cancelled) setResult({ slug, forecast });
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  // A result for a ward the reader has since left counts as still loading.
  const current = result?.slug === slug ? result : null;
  const forecast = current?.forecast ?? null;
  // "2026-11-04T10:00" is local time in the city's timezone. The response can be a
  // few minutes old (it is cached), so the panel says when the reading was taken.
  const readingTime = forecast?.observedAt.match(/T(\d{2}:\d{2})/)?.[1];

  return (
    <div>
      <p className="kicker">Weather at this ward&apos;s centre</p>
      {!current && <p className="mt-2 text-xs text-muted-foreground">Loading weather.</p>}
      {current && !forecast && (
        <p className="mt-2 text-xs text-muted-foreground">Weather unavailable right now.</p>
      )}
      {forecast && (
        <>
          <p className="mt-2 text-sm text-foreground">
            <span className="font-mono font-medium">{forecast.temperatureC.toFixed(1)}°C</span>, feels like{" "}
            <span className="font-mono font-medium">{forecast.apparentC.toFixed(1)}°C</span>
          </p>
          {readingTime && (
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              Reading from {readingTime} {ACTIVE_CITY.name} time
            </p>
          )}
          <ul className="mt-2.5 grid grid-cols-7 gap-1 text-center">
            {forecast.days.map((day) => {
              const name = weekday(day.date);
              const max = Math.round(day.maxC);
              const min = Math.round(day.minC);
              return (
                <li key={day.date} aria-label={`${name}: high ${max}, low ${min} degrees`}>
                  <span className="block text-[10px] text-muted-foreground">{name}</span>
                  <span className="block font-mono text-xs text-foreground">{max}°</span>
                  <span className="block font-mono text-[11px] text-muted-foreground">{min}°</span>
                </li>
              );
            })}
          </ul>
        </>
      )}
      <p className="mt-2 text-[11px] text-muted-foreground">{WEATHER_LABEL}</p>
    </div>
  );
}
