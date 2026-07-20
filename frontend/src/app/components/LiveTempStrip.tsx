"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Thermometer } from "lucide-react";
import { fetchMumbaiTemp } from "@/lib/weather";

type Status = "loading" | "ok" | "unavailable";

/**
 * Live Mumbai air temperature (Open-Meteo), framed as a methodology point rather
 * than a decorative weather widget: it exists to make UCIP's own stated
 * LST-is-not-air-temperature limitation tangible with a real, live contrast.
 * On any fetch failure this shows an honest "unavailable" state — never a
 * stale or fabricated number.
 */
export default function LiveTempStrip() {
  const [status, setStatus] = useState<Status>("loading");
  const [tempC, setTempC] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchMumbaiTemp().then((result) => {
      if (cancelled) return;
      if (result) {
        setTempC(result.temperatureC);
        setStatus("ok");
      } else {
        setStatus("unavailable");
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-2">
      <span className="inline-flex w-fit items-center gap-2 rounded-full border border-border bg-surface/85 px-3 py-1.5 text-sm backdrop-blur-sm">
        <span className="relative flex h-2 w-2 shrink-0" aria-hidden>
          {status === "ok" && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-emerald/70" />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${
              status === "ok" ? "bg-brand-emerald" : "bg-muted-foreground"
            }`}
          />
        </span>
        <Thermometer className="h-4 w-4 shrink-0 text-brand-teal" aria-hidden />
        {status === "loading" && <span className="text-foreground">Checking Mumbai now…</span>}
        {status === "ok" && tempC !== null && (
          <span className="text-foreground">
            Mumbai now{" "}
            <span className="font-mono font-medium text-foreground">{tempC.toFixed(1)}°C</span> air
          </span>
        )}
        {status === "unavailable" && (
          <span className="text-foreground">Live air temperature unavailable</span>
        )}
      </span>
      <span className="hero-text-shadow max-w-md text-xs leading-relaxed text-foreground">
        The map measures land-surface temperature, a related but different number.{" "}
        <Link href="/methodology#limitations" className="font-semibold text-foreground underline">
          See why that matters
        </Link>
        .
      </span>
    </div>
  );
}
