/**
 * Pure GeoJSON geometry helpers, used by the dashboard map to frame a selected
 * ward.
 *
 * Extracted from WardChoropleth.tsx (issue #42): both functions are pure, depend
 * on neither Leaflet nor the DOM, and were only living in a component file
 * because that is where they were first needed. Here they can be tested against
 * real ward polygons without mounting a map.
 */

import type { Geometry, Position } from "geojson";

/**
 * Flattens any GeoJSON Polygon/MultiPolygon ring nesting down to raw [lng, lat]
 * pairs.
 *
 * Deliberately structural rather than type-driven: it recurses until it finds an
 * array whose first element is a number, so it handles Polygon (3 levels),
 * MultiPolygon (4 levels), and the bare coordinate arrays in between without
 * needing to know which it was given. Anything that is not an array, including
 * the empty coordinate arrays GeoJSON permits, yields nothing rather than
 * throwing, because a malformed feature should drop out of the bounds
 * calculation rather than break the whole map.
 */
export function flattenPositions(coords: unknown): Position[] {
  if (!Array.isArray(coords)) return [];
  if (typeof coords[0] === "number") return [coords as Position];
  return (coords as unknown[]).flatMap(flattenPositions);
}

/**
 * Bounding box of a Polygon or MultiPolygon as [[minLat, minLng], [maxLat, maxLng]],
 * the order Leaflet's LatLngBounds expects (note this is the reverse of GeoJSON's
 * own [lng, lat] position order).
 *
 * Returns null for any other geometry type and for geometries with no positions,
 * so callers can skip framing rather than fly the map to NaN.
 */
export function boundsOf(geometry: Geometry): [[number, number], [number, number]] | null {
  if (geometry.type !== "Polygon" && geometry.type !== "MultiPolygon") return null;
  const positions = flattenPositions(geometry.coordinates);
  if (positions.length === 0) return null;
  const lats = positions.map((p) => p[1]);
  const lngs = positions.map((p) => p[0]);
  return [
    [Math.min(...lats), Math.min(...lngs)],
    [Math.max(...lats), Math.max(...lngs)],
  ];
}
