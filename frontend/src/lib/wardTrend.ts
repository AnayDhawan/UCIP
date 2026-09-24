/**
 * Per-ward multi-year trend, as published by pipeline/14_timeseries.py (#89).
 *
 * The honest framing matters more than the chart here. The issue asked to
 * classify each ward as warming, cooling, greening or losing green. On the
 * current record none of the 24 wards has a statistically significant trend in
 * either measure: `n_wards_significant` is 0. Printing a "warming" badge would
 * be inventing a finding the data does not support, so the UI shows the series
 * that exists, the fitted slope with its uncertainty, and says plainly when
 * the slope cannot be distinguished from noise.
 *
 * That is not a null result to hide. "Thirteen dry seasons of Landsat show no
 * detectable ward-level trend" is a real statement, and a more defensible one
 * than a coloured arrow.
 */

import en from "./i18n/dictionaries/en";
import { format, type Dictionary } from "./i18n";

export type TrendPoint = { year: number; LST_C: number | null; NDVI: number | null };

export type WardTrend = {
  ward_id: string;
  n_years: number;
  trend: {
    lst_c_per_decade: number;
    lst_stderr_c_per_decade: number;
    lst_p_value: number;
    lst_r_squared: number;
    lst_significant: boolean;
    ndvi_per_decade: number;
    ndvi_p_value: number;
    ndvi_significant: boolean;
    classification: string;
  };
  series: TrendPoint[];
};

export type TimeSeries = {
  years: number[];
  measures: string[];
  limitations: string[];
  wards: WardTrend[];
  summary: {
    n_wards_fitted: number;
    n_wards_significant: number;
    warming: number;
    cooling: number;
    no_detected_trend: number;
  };
};

/** Points for one measure, dropping years the pipeline could not fit. */
export function seriesFor(ward: WardTrend, measure: "LST_C" | "NDVI"): Array<{ year: number; value: number }> {
  return ward.series
    .map((point) => ({ year: point.year, value: point[measure] }))
    .filter((point): point is { year: number; value: number } => typeof point.value === "number");
}

/**
 * An SVG polyline path for a sparkline, scaled to its own range.
 *
 * Deliberately self-scaled rather than zero-based. A sparkline exists to show
 * shape, and anchoring a 30-34 degree series to zero flattens it into a
 * straight line that says nothing. The label carries the absolute numbers, so
 * the axis is not load-bearing.
 */
export function sparklinePath(
  points: Array<{ year: number; value: number }>,
  width: number,
  height: number
): string {
  if (points.length === 0) return "";
  if (points.length === 1) return `M0,${height / 2}L${width},${height / 2}`;

  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;

  return points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      // A flat series has no range to scale against; draw it down the middle
      // rather than dividing by zero.
      const y = span === 0 ? height / 2 : height - ((point.value - min) / span) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join("");
}

/**
 * How to describe a fitted slope in one line.
 *
 * A slope that is not significant is reported as "no detected trend" with the
 * estimate in brackets, rather than as a direction. The estimate is still
 * shown, because hiding it would overstate the certainty in the other
 * direction.
 */
export function describeSlope(
  perDecade: number,
  significant: boolean,
  unit: string,
  rising: string,
  falling: string,
  t: Dictionary = en
): string {
  const magnitude = format(t.trend.perDecade, { value: Math.abs(perDecade).toFixed(2), unit });
  if (!significant) {
    return format(t.trend.noTrend, { value: `${perDecade >= 0 ? "+" : "-"}${magnitude}` });
  }
  return `${perDecade >= 0 ? rising : falling} ${magnitude}`;
}
