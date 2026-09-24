"use client";

import type { Geometry, Position } from "geojson";
import { boundsOf } from "@/lib/geometry";
import { hviColor } from "@/lib/hvi";
import { useLocale } from "@/lib/i18n/LocaleProvider";

function rings(geometry: Geometry): Position[][] {
  if (geometry.type === "Polygon") return geometry.coordinates;
  if (geometry.type === "MultiPolygon") return geometry.coordinates.flat();
  return [];
}

/** A dependency-free SVG fallback for print: it is the actual ward boundary,
 * not a remote tile that may disappear while a planner is making a PDF. */
export default function WardStaticMap({ geometry, hvi, label }: { geometry: Geometry; hvi: number | null; label: string }) {
  const { t, f } = useLocale();
  const bounds = boundsOf(geometry);
  if (!bounds) return null;
  const [[minLat, minLng], [maxLat, maxLng]] = bounds;
  const width = maxLng - minLng || 1;
  const height = maxLat - minLat || 1;
  const path = rings(geometry)
    .map((ring) =>
      ring
        .map(([lng, lat], index) => `${index === 0 ? "M" : "L"}${((lng - minLng) / width) * 100} ${100 - ((lat - minLat) / height) * 100}`)
        .join(" ")
    )
    .join(" ");

  return (
    <figure className="ward-static-map" aria-label={f(t.ward.mapOf, { label })}>
      <svg viewBox="0 0 100 100" role="img" aria-hidden="true" preserveAspectRatio="xMidYMid meet">
        <path d={path} fill={hviColor(hvi)} fillRule="evenodd" stroke="currentColor" strokeWidth="1.2" />
      </svg>
      <figcaption>{f(t.ward.boundary, { label })}</figcaption>
    </figure>
  );
}
