/**
 * Server-side reads of the committed ward snapshots in public/, for the ward
 * page, its share card and the weather route. Node-only (node:fs), so client
 * code must not import it. Reads public/ through process.cwd(), the same way the
 * embed card and the v1 API routes do.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { WardProps } from "./wardTypes";
import { wardIdFromSlug } from "./wardSlug";

/** A snapshot file, or null when it is absent or unreadable. */
export function readPublicJson<T>(filename: string): T | null {
  try {
    return JSON.parse(readFileSync(join(process.cwd(), "public", filename), "utf8")) as T;
  } catch {
    return null;
  }
}

/** All wards, as written by pipeline/05_hvi.py. Required: the site has nothing to show without it. */
export const wardFeatures = (
  JSON.parse(readFileSync(join(process.cwd(), "public", "wards_hvi.geojson"), "utf8")) as FeatureCollection<
    Geometry,
    WardProps
  >
).features;

/** The ward for a /ward/<slug> segment, or null for an unknown or malformed slug. */
export function wardFromSlug(slug: string): Feature<Geometry, WardProps> | null {
  const id = wardIdFromSlug(slug);
  return wardFeatures.find(({ properties }) => properties.ward_id === id) ?? null;
}
