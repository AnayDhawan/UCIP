/**
 * Shape of `public/hero_city.json`, written by pipeline/11_hero_city.py.
 *
 * Coordinates are already projected (UTM 43N), simplified, centred and scaled
 * so the longer axis spans 2.0 units; the renderer treats them as unitless.
 * Outer rings are counter-clockwise and holes clockwise, which is what
 * THREE.Shape needs to punch holes correctly.
 */

export type HeroPart = {
  outer: [number, number][];
  holes: [number, number][][];
};

export type HeroCityWard = {
  ward_id: string;
  ward_gid: number;
  hvi: number | null;
  rank: number | null;
  parts: HeroPart[];
};

export type HeroCityData = {
  generated_from: string;
  projection: string;
  simplify_tolerance_m: number;
  note: string;
  extent: { width: number; height: number };
  wards: HeroCityWard[];
};

/**
 * Shape of `public/hero_region.json`, written by pipeline/12_hero_region.py.
 * Natural Earth 1:10m coastline clipped to a disc around Mumbai, in the same
 * model space as the ward geometry above. Coarse on purpose: it is only ever
 * rendered as unlit, hazed context.
 */
export type HeroRegionData = {
  generated_from: string;
  licence: string;
  source_url: string;
  projection: string;
  region_radius_units: number;
  simplify_tolerance_m: number;
  note: string;
  parts: HeroPart[];
};

export const HERO_CITY_URL = "/hero_city.json";
export const HERO_REGION_URL = "/hero_region.json";
