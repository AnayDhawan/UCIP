/**
 * Issue #42. Fixtures are real ward geometry read from the committed
 * wards_hvi.geojson rather than hand-written toy coordinates, because the whole
 * point of these helpers is surviving the actual nesting depth and ring counts
 * the pipeline emits.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Feature, FeatureCollection, Geometry, Polygon, MultiPolygon } from "geojson";
import { flattenPositions, boundsOf } from "./geometry";

const wardsGeo = JSON.parse(
  readFileSync(join(process.cwd(), "public", "wards_hvi.geojson"), "utf8")
) as FeatureCollection<Geometry, { ward_id: string }>;

/** Mumbai's real extent, from the pipeline's own plausibility check in 01_grid.py. */
const MUMBAI_LNG = [72.7, 73.0] as const;
const MUMBAI_LAT = [18.8, 19.3] as const;

describe("flattenPositions", () => {
  it("returns a single position for a bare coordinate pair", () => {
    expect(flattenPositions([72.8, 19.1])).toEqual([[72.8, 19.1]]);
  });

  it("flattens a Polygon's ring nesting to raw positions", () => {
    const polygon = [
      [
        [72.8, 19.0],
        [72.9, 19.0],
        [72.9, 19.1],
        [72.8, 19.0],
      ],
    ];
    expect(flattenPositions(polygon)).toEqual([
      [72.8, 19.0],
      [72.9, 19.0],
      [72.9, 19.1],
      [72.8, 19.0],
    ]);
  });

  it("flattens a MultiPolygon's deeper nesting to the same flat shape", () => {
    const multi = [
      [
        [
          [72.8, 19.0],
          [72.9, 19.0],
        ],
      ],
      [
        [
          [72.95, 19.2],
          [72.96, 19.25],
        ],
      ],
    ];
    expect(flattenPositions(multi)).toEqual([
      [72.8, 19.0],
      [72.9, 19.0],
      [72.95, 19.2],
      [72.96, 19.25],
    ]);
  });

  it("preserves interior rings rather than only reading the exterior", () => {
    const withHole = [
      [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 0],
      ],
      [
        [2, 2],
        [3, 2],
        [3, 3],
        [2, 2],
      ],
    ];
    expect(flattenPositions(withHole)).toHaveLength(8);
  });

  it("returns nothing for non-arrays and empty arrays instead of throwing", () => {
    expect(flattenPositions(null)).toEqual([]);
    expect(flattenPositions(undefined)).toEqual([]);
    expect(flattenPositions("F/N")).toEqual([]);
    expect(flattenPositions(42)).toEqual([]);
    expect(flattenPositions([])).toEqual([]);
  });

  it("flattens every real ward polygon to plausible Mumbai coordinates", () => {
    for (const feature of wardsGeo.features) {
      const geom = feature.geometry as Polygon | MultiPolygon;
      const positions = flattenPositions(geom.coordinates);
      expect(positions.length).toBeGreaterThan(0);
      for (const [lng, lat] of positions) {
        expect(lng).toBeGreaterThanOrEqual(MUMBAI_LNG[0]);
        expect(lng).toBeLessThanOrEqual(MUMBAI_LNG[1]);
        expect(lat).toBeGreaterThanOrEqual(MUMBAI_LAT[0]);
        expect(lat).toBeLessThanOrEqual(MUMBAI_LAT[1]);
      }
    }
  });
});

describe("boundsOf", () => {
  it("computes bounds as [[minLat, minLng], [maxLat, maxLng]]", () => {
    const polygon: Polygon = {
      type: "Polygon",
      coordinates: [
        [
          [72.8, 19.0],
          [72.95, 19.0],
          [72.95, 19.2],
          [72.8, 19.2],
          [72.8, 19.0],
        ],
      ],
    };
    expect(boundsOf(polygon)).toEqual([
      [19.0, 72.8],
      [19.2, 72.95],
    ]);
  });

  it("spans every part of a MultiPolygon, not just the first", () => {
    const multi: MultiPolygon = {
      type: "MultiPolygon",
      coordinates: [
        [
          [
            [72.8, 19.0],
            [72.85, 19.05],
            [72.8, 19.0],
          ],
        ],
        [
          [
            [72.9, 19.2],
            [72.95, 19.25],
            [72.9, 19.2],
          ],
        ],
      ],
    };
    expect(boundsOf(multi)).toEqual([
      [19.0, 72.8],
      [19.25, 72.95],
    ]);
  });

  it("returns null for geometry types that have no area", () => {
    expect(boundsOf({ type: "Point", coordinates: [72.8, 19.0] })).toBeNull();
    expect(
      boundsOf({
        type: "LineString",
        coordinates: [
          [72.8, 19.0],
          [72.9, 19.1],
        ],
      })
    ).toBeNull();
  });

  it("returns null rather than NaN bounds for an empty polygon", () => {
    // Math.min() of an empty array is Infinity, so without the length guard this
    // would fly the map to an infinite bounding box.
    expect(boundsOf({ type: "Polygon", coordinates: [] })).toBeNull();
  });

  it("returns real, ordered bounds inside Mumbai for every ward", () => {
    for (const feature of wardsGeo.features as Feature<Polygon | MultiPolygon>[]) {
      const bounds = boundsOf(feature.geometry);
      expect(bounds).not.toBeNull();
      const [[minLat, minLng], [maxLat, maxLng]] = bounds!;
      expect(minLat).toBeLessThanOrEqual(maxLat);
      expect(minLng).toBeLessThanOrEqual(maxLng);
      expect(Number.isFinite(minLat)).toBe(true);
      expect(Number.isFinite(maxLng)).toBe(true);
      expect(minLat).toBeGreaterThanOrEqual(MUMBAI_LAT[0]);
      expect(maxLat).toBeLessThanOrEqual(MUMBAI_LAT[1]);
    }
  });
});
