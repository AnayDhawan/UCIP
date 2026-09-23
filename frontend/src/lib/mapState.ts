/** URL-safe state for the dashboard's Leaflet view. */

export const MAP_LAYERS = ["hvi", "hvi_grid", "plantability", "ndvi_change"] as const;
export type MapLayer = (typeof MAP_LAYERS)[number];

export type MapView = { lat: number; lng: number; zoom: number };

function finiteIn(value: string | null, min: number, max: number): number | null {
  if (value === null || value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= min && parsed <= max ? parsed : null;
}

export function parseMapLayer(value: string | null): MapLayer {
  return MAP_LAYERS.includes(value as MapLayer) ? (value as MapLayer) : "hvi";
}

/** Returns null unless all three parts are present and geographically valid. */
export function parseMapView(params: Pick<URLSearchParams, "get">): MapView | null {
  const lat = finiteIn(params.get("lat"), -90, 90);
  const lng = finiteIn(params.get("lng"), -180, 180);
  const zoom = finiteIn(params.get("zoom"), 0, 20);
  return lat === null || lng === null || zoom === null ? null : { lat, lng, zoom };
}

export function writeMapView(params: URLSearchParams, view: MapView): void {
  params.set("lat", String(view.lat));
  params.set("lng", String(view.lng));
  params.set("zoom", String(view.zoom));
}
