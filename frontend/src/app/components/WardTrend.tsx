"use client";

/**
 * Thirteen dry seasons of land surface temperature and green cover, as a pair
 * of sparklines in the ward dialog (issue #89).
 *
 * Shows the series and the fitted slope. It does not show a direction badge,
 * because on the current record no ward has a statistically significant trend
 * in either measure, and a coloured arrow would assert one. See
 * lib/wardTrend.ts for the reasoning.
 */

import { useEffect, useState } from "react";
import {
  describeSlope,
  seriesFor,
  sparklinePath,
  type TimeSeries,
  type WardTrend as WardTrendRecord,
} from "@/lib/wardTrend";

const WIDTH = 96;
const HEIGHT = 24;

function Sparkline({
  points,
  label,
}: {
  points: Array<{ year: number; value: number }>;
  label: string;
}) {
  if (points.length < 2) return null;

  const first = points[0]!;
  const last = points[points.length - 1]!;

  return (
    <svg
      width={WIDTH}
      height={HEIGHT}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={`${label}: ${first.value} in ${first.year} to ${last.value} in ${last.year}`}
      className="overflow-visible text-brand-teal"
    >
      <path
        d={sparklinePath(points, WIDTH, HEIGHT)}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function WardTrend({ wardId }: { wardId: string }) {
  const [data, setData] = useState<TimeSeries | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/ward_timeseries.json")
      .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
      .then((json: TimeSeries) => {
        if (!cancelled) setData(json);
      })
      .catch(() => {
        // Additive: a missing time series must not take the dialog down with
        // it, the same way the ward profile fetch is treated.
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed || !data) return null;

  const ward: WardTrendRecord | undefined = data.wards.find((w) => w.ward_id === wardId);
  if (!ward) return null;

  const lst = seriesFor(ward, "LST_C");
  const ndvi = seriesFor(ward, "NDVI");
  if (lst.length < 2 && ndvi.length < 2) return null;

  const { trend } = ward;

  return (
    <section className="mt-4 border-t border-border pt-4">
      <h4 className="text-sm font-semibold text-foreground">
        Since {data.years[0]}
      </h4>

      {/* dl > div > (dt, dd) is the only wrapper the spec allows inside a
          definition list. An earlier version nested a second div around the
          dt/dd pair to lay the sparkline out beside it, which axe flags as
          definition-list and dlitem, both serious. The sparkline lives in the
          dd instead, which is also the more honest markup: the chart is part
          of the value, not a sibling of it. */}
      <dl className="mt-3 space-y-3">
        <div>
          <dt className="text-xs uppercase tracking-wide text-muted-foreground">
            Surface temperature
          </dt>
          <dd className="flex items-center justify-between gap-3 text-sm text-foreground">
            <span>
              {describeSlope(trend.lst_c_per_decade, trend.lst_significant, "C", "warming", "cooling")}
            </span>
            <Sparkline points={lst} label="Dry-season land surface temperature" />
          </dd>
        </div>

        <div>
          <dt className="text-xs uppercase tracking-wide text-muted-foreground">Green cover</dt>
          <dd className="flex items-center justify-between gap-3 text-sm text-foreground">
            <span>
              {describeSlope(trend.ndvi_per_decade, trend.ndvi_significant, "NDVI", "greening", "losing green")}
            </span>
            <Sparkline points={ndvi} label="Dry-season NDVI" />
          </dd>
        </div>
      </dl>

      <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
        {trend.lst_significant || trend.ndvi_significant ? (
          <>Least-squares slope over {ward.n_years} dry seasons. It describes the observed period, not a forecast.</>
        ) : (
          <>
            {ward.n_years} dry seasons of Landsat show no trend distinguishable from
            year-to-year variation in this ward. The sparklines are the real
            measurements; the slope is shown for completeness, not as a finding.
          </>
        )}
      </p>
    </section>
  );
}
