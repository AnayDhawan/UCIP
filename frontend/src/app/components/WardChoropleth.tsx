"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useMemo, useRef, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import { geoJSON as leafletGeoJSON } from "leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { GeoJSON as LeafletGeoJSONLayer, Layer, Path, PathOptions } from "leaflet";
import { Maximize2, Minimize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { boundsOf } from "@/lib/geometry";
import { hviColor as colorForHvi } from "@/lib/hvi";
import type { CellNbsProps, CellNdviProps, WardProps } from "@/lib/wardTypes";

type LayerId = "hvi" | "plantability" | "ndvi_change";

const MUMBAI_CENTER: [number, number] = [19.076, 72.877];

/** Selected-ward outline, layered on top of whichever data layer is active. */
function selectionStyle(wardId: string, selectedWardId: string | null): Partial<PathOptions> {
  if (wardId !== selectedWardId) return {};
  return { color: "#0EA5B3", weight: 3 };
}

function styleHvi(selectedWardId: string | null) {
  return (feature?: Feature<Geometry, WardProps>): PathOptions => ({
    fillColor: colorForHvi(feature?.properties?.HVI ?? null),
    fillOpacity: 0.75,
    color: "#333333",
    weight: 1,
    ...selectionStyle(feature?.properties?.ward_id ?? "", selectedWardId),
  });
}

function stylePlantability(selectedWardId: string | null) {
  return (feature?: Feature<Geometry, CellNbsProps>): PathOptions => {
    const plantable = feature?.properties?.plantable;
    return {
      fillColor: plantable ? "#4ade80" : "#f87171",
      fillOpacity: 0.65,
      color: "#333333",
      weight: 0.5,
      ...selectionStyle(feature?.properties?.ward_id ?? "", selectedWardId),
    };
  };
}

const NDVI_CHANGE_COLORS: Record<string, string> = {
  gained: "#4ade80",
  stable: "#d4d4d8",
  lost: "#f87171",
  unknown: "#e5e5e5",
};

function styleNdviChange(selectedWardId: string | null) {
  return (feature?: Feature<Geometry, CellNdviProps>): PathOptions => {
    const cls = feature?.properties?.change_class ?? "unknown";
    return {
      fillColor: NDVI_CHANGE_COLORS[cls] ?? "#e5e5e5",
      fillOpacity: 0.7,
      color: "#333333",
      weight: 0.5,
      ...selectionStyle(feature?.properties?.ward_id ?? "", selectedWardId),
    };
  };
}

const LAYER_META: Record<LayerId, { label: string; url: string; caption: string }> = {
  hvi: {
    label: "Heat vulnerability",
    url: "/wards_hvi.geojson",
    caption: "How urgently each ward needs cooling, combining heat, people, and access to help.",
  },
  plantability: {
    label: "Plantability",
    url: "/cells_nbs.geojson",
    caption: "Where planting trees makes ecological sense, and where cool roofs work better.",
  },
  ndvi_change: {
    label: "Green-cover change",
    url: "/cells_ndvi_change.geojson",
    caption: "Where vegetation has grown or been lost since the 2016-17 dry season.",
  },
};

const HVI_LEGEND_BINS = [
  { color: "#ffffb2", label: "Under 20" },
  { color: "#fed976", label: "20-35" },
  { color: "#feb24c", label: "35-50" },
  { color: "#fd8d3c", label: "50-65" },
  { color: "#f03b20", label: "65-80" },
  { color: "#bd0026", label: "80+" },
];

function Legend({ layer }: { layer: LayerId }) {
  return (
    <Card className="absolute bottom-6 left-2 z-[1000] max-w-[240px] gap-0 bg-background/95 p-3 text-xs backdrop-blur-sm">
      {layer === "hvi" && (
        <>
          <p className="mb-1.5 font-semibold text-foreground">Heat Vulnerability Index (0-100)</p>
          <div className="flex overflow-hidden rounded-sm" aria-hidden="true">
            {HVI_LEGEND_BINS.map((b) => (
              <div key={b.color} className="h-3 flex-1" style={{ background: b.color }} />
            ))}
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
            <span>Less vulnerable</span>
            <span>Most vulnerable</span>
          </div>
        </>
      )}
      {layer === "plantability" && (
        <>
          <p className="mb-1.5 font-semibold text-foreground">Can trees go here?</p>
          <div className="space-y-1 text-foreground">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: "#4ade80" }} aria-hidden="true" />
              <span>Yes, suitable for planting</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: "#f87171" }} aria-hidden="true" />
              <span>No, cool roofs instead</span>
            </div>
          </div>
        </>
      )}
      {layer === "ndvi_change" && (
        <>
          <p className="mb-1.5 font-semibold text-foreground">Green cover since 2016-17</p>
          <div className="space-y-1 text-foreground">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: "#4ade80" }} aria-hidden="true" />
              <span>Gained vegetation</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm border border-border" style={{ background: "#d4d4d8" }} aria-hidden="true" />
              <span>Stable</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: "#f87171" }} aria-hidden="true" />
              <span>Lost vegetation</span>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}

/** Pans/zooms to the selected ward when selection changes and ward-level geometry is available. */
function FlyToSelection({
  selectedWardId,
  wardsGeo,
}: {
  selectedWardId: string | null;
  wardsGeo: FeatureCollection<Geometry, WardProps> | null;
}) {
  const map = useMap();
  useEffect(() => {
    if (!selectedWardId || !wardsGeo) return;
    const feature = wardsGeo.features.find((f) => f.properties.ward_id === selectedWardId);
    const bounds = feature ? boundsOf(feature.geometry) : null;
    if (bounds) map.flyToBounds(bounds, { padding: [48, 48], maxZoom: 13, duration: 0.6 });
  }, [selectedWardId, wardsGeo, map]);
  return null;
}

/**
 * Leaflet caches its container's pixel size at creation time and doesn't notice
 * layout-driven resizes (e.g. toggling fullscreen, which changes the container's
 * width instantly via React state, not a window resize event). Without this the
 * map keeps its old framing and leaves the newly-available space blank.
 */
function InvalidateSizeOnChange({ dep }: { dep: unknown }) {
  const map = useMap();

  // Primary mechanism: react to the container's actual pixel size changing,
  // whatever the cause (fullscreen toggle, sidebar mount/unmount, a CSS
  // transition settling, OS/browser chrome changing). This is more reliable
  // than guessing a fixed delay, since it fires exactly when the size is
  // actually different rather than assuming a transition duration.
  useEffect(() => {
    const el = map.getContainer();
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(el);
    return () => observer.disconnect();
  }, [map]);

  // Redundant safety net tied to the fullscreen toggle itself, in case a
  // resize happens to report the same size mid-transition before settling
  // (e.g. a layout that overshoots then corrects).
  useEffect(() => {
    map.invalidateSize();
    const ids = [60, 260].map((ms) => window.setTimeout(() => map.invalidateSize(), ms));
    return () => ids.forEach(window.clearTimeout);
  }, [dep, map]);

  return null;
}

/**
 * Frames the map to the 24 wards' actual extent once their geometry loads,
 * instead of a fixed center/zoom that leaves most of the view as surrounding
 * Thane/Panvel/ocean. Runs once (a ref guard, not state) so it never fights
 * a user's own pan/zoom or the ward-selection FlyToSelection above.
 */
function FitToWardExtent({ wardsGeo }: { wardsGeo: FeatureCollection<Geometry, WardProps> | null }) {
  const map = useMap();
  const fitted = useRef(false);
  useEffect(() => {
    if (fitted.current || !wardsGeo) return;
    const bounds = leafletGeoJSON(wardsGeo as GeoJSON.GeoJsonObject).getBounds();
    if (bounds.isValid()) {
      // Tight padding plus the map's fractional zoomSnap: with the default
      // whole-number snap, fitBounds rounds down and can throw away most of a
      // zoom level, leaving the city noticeably smaller than the space allows.
      map.fitBounds(bounds, { padding: [10, 10] });
      fitted.current = true;
    }
  }, [wardsGeo, map]);
  return null;
}

/** react-leaflet's MapContainer doesn't forward aria-label to the underlying
 *  container div, so screen readers otherwise announce only the zoom
 *  buttons/attribution text with no indication this is a heat-vulnerability
 *  map. Set it imperatively on the real DOM node instead. */
function MapAccessibleName() {
  const map = useMap();
  useEffect(() => {
    map.getContainer().setAttribute("aria-label", "Mumbai ward heat vulnerability map");
  }, [map]);
  return null;
}

export default function WardChoropleth({
  selectedWardId = null,
  onSelectWard,
  isFullscreen = false,
  onToggleFullscreen,
}: {
  selectedWardId?: string | null;
  onSelectWard?: (wardId: string) => void;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}) {
  const [activeLayer, setActiveLayer] = useState<LayerId>("hvi");
  const [cache, setCache] = useState<Partial<Record<LayerId, FeatureCollection>>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cache[activeLayer]) return;
    fetch(LAYER_META[activeLayer].url)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((data) => setCache((prev) => ({ ...prev, [activeLayer]: data })))
      .catch((err) => setError(String(err)));
  }, [activeLayer, cache]);

  const data = cache[activeLayer];
  const wardsGeo = (cache.hvi as FeatureCollection<Geometry, WardProps> | undefined) ?? null;

  // Memoize per-render style functions so react-leaflet sees a stable identity
  // unless selectedWardId actually changed (#35). Otherwise every render
  // creates a new function and forces an unnecessary GeoJSON restyle.
  const hviStyle = useMemo(() => styleHvi(selectedWardId), [selectedWardId]);
  const plantabilityStyle = useMemo(() => stylePlantability(selectedWardId), [selectedWardId]);
  const ndviStyle = useMemo(() => styleNdviChange(selectedWardId), [selectedWardId]);

  // Selection changes restyle the already-mounted layer in place via the ref
  // below, and never go through `key`. Remounting on every ward click tears the
  // layer down and recreates it mid-click, which silently swallows whatever
  // Leaflet was doing with that same click. The popup this originally protected
  // is gone (WardDialog covers fullscreen too), but the hazard is not: keep
  // `key` for changes that genuinely need onEachFeature to rebind.
  const layerRef = useRef<LeafletGeoJSONLayer | null>(null);
  useEffect(() => {
    if (!layerRef.current) return;
    if (activeLayer === "hvi") layerRef.current.setStyle(hviStyle as (f?: Feature<Geometry>) => PathOptions);
    else if (activeLayer === "plantability")
      layerRef.current.setStyle(plantabilityStyle as (f?: Feature<Geometry>) => PathOptions);
    else layerRef.current.setStyle(ndviStyle as (f?: Feature<Geometry>) => PathOptions);
  }, [hviStyle, plantabilityStyle, ndviStyle, activeLayer]);

  /** Every layer resolves a click to a ward: the cell layers carry `ward_id`
   *  too, so clicking a grid cell opens its parent ward. */
  function selectFrom<P extends { ward_id: string }>(feature: Feature<Geometry, P>, layer: Layer) {
    const wardId = feature.properties.ward_id;
    layer.on("click", () => onSelectWard?.(wardId));

    // Keyboard access: Leaflet path layers render as SVG <path> elements that
    // are not focusable by default. Make each one tabbable and select it on
    // Enter/Space, mirroring the click handler. The focus ring is drawn with
    // CSS (see the global rule below) so it stays visible without touching
    // Leaflet's own styling.
    // Leaflet calls onEachFeature *before* the layer is added to the map, so
    // getElement() is undefined at this point — defer until the 'add' event
    // when the <path> actually exists in the DOM.
    const pathLayer = layer as Path;
    const attachKeyboard = () => {
      const el = pathLayer.getElement?.() as HTMLElement | undefined;
      if (!el) return;
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
      el.setAttribute("aria-label", `Select ward ${wardId}`);
      const onKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelectWard?.(wardId);
        }
      };
      el.addEventListener("keydown", onKeyDown);
      layer.once("remove", () => el.removeEventListener("keydown", onKeyDown));
    };
    layer.once("add", attachKeyboard);
  }

  return (
    <div className="absolute inset-0">
      <Card className="absolute right-2 top-2 z-[1000] w-fit gap-0 bg-background/95 p-1 backdrop-blur-sm">
        <div className="flex items-center gap-0.5">
          <Tabs value={activeLayer} onValueChange={(v: string) => setActiveLayer(v as LayerId)}>
            {/* Height is overridden through the same group-data variant the
                primitive uses, so it wins rather than sitting alongside it. */}
            <TabsList aria-label="Map layer" className="group-data-horizontal/tabs:h-7">
              {(Object.keys(LAYER_META) as LayerId[]).map((id) => (
                <TabsTrigger
                  key={id}
                  value={id}
                  title={LAYER_META[id].caption}
                  className="whitespace-nowrap px-1.5 text-xs"
                >
                  {LAYER_META[id].label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          {onToggleFullscreen && (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onToggleFullscreen}
              aria-label={isFullscreen ? "Exit fullscreen" : "View map fullscreen"}
              title={isFullscreen ? "Exit fullscreen (Esc)" : "View fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="h-3.5 w-3.5" />
              ) : (
                <Maximize2 className="h-3.5 w-3.5" />
              )}
            </Button>
          )}
        </div>
      </Card>

      <Legend layer={activeLayer} />

      {error && (
        <div className="absolute inset-x-0 top-12 z-[1000] mx-auto w-fit rounded bg-destructive/10 px-3 py-1 text-sm text-destructive">
          Failed to load layer: {error}
        </div>
      )}

      <MapContainer
        center={MUMBAI_CENTER}
        zoom={11}
        // Quarter-step zooms so fitBounds can actually fill the container
        // instead of rounding down to the next whole level.
        zoomSnap={0.25}
        zoomDelta={0.5}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {data && activeLayer === "hvi" && (
          <GeoJSON
            key={`hvi-${isFullscreen}`}
            ref={layerRef}
            data={data as FeatureCollection<Geometry, WardProps>}
            style={hviStyle as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "plantability" && (
          <GeoJSON
            key={`plantability-${isFullscreen}`}
            ref={layerRef}
            data={data as FeatureCollection<Geometry, CellNbsProps>}
            style={plantabilityStyle as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "ndvi_change" && (
          <GeoJSON
            key={`ndvi_change-${isFullscreen}`}
            ref={layerRef}
            data={data as FeatureCollection<Geometry, CellNdviProps>}
            style={ndviStyle as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        <FlyToSelection selectedWardId={selectedWardId} wardsGeo={wardsGeo} />
        <InvalidateSizeOnChange dep={isFullscreen} />
        <FitToWardExtent wardsGeo={wardsGeo} />
        <MapAccessibleName />
      </MapContainer>
    </div>
  );
}
