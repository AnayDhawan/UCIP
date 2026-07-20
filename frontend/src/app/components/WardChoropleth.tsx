"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import { geoJSON as leafletGeoJSON } from "leaflet";
import type { Feature, FeatureCollection, Geometry, Position } from "geojson";
import type { GeoJSON as LeafletGeoJSONLayer, LatLngBoundsExpression, Layer, PathOptions } from "leaflet";
import { Maximize2, Minimize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { matchCitationFromText } from "@/lib/citations";
import { areasForWard } from "@/lib/wardAreas";

type NbsRec = {
  ward_id: string;
  intervention: string;
  rationale: string;
  citation: string;
  priority: number;
};

type WardProps = {
  ward_id: string;
  ward_gid: number;
  HVI: number | null;
  rank: number | null;
  n_cells: number | null;
  [key: string]: unknown;
};

type CellNbsProps = {
  grid_id: string;
  ward_id: string;
  plantable: boolean;
  worldcover_class: number | null;
  nbs_fired: boolean;
  [key: string]: unknown;
};

type CellNdviProps = {
  grid_id: string;
  ward_id: string;
  ndvi_delta: number | null;
  change_class: "gained" | "stable" | "lost" | "unknown";
  [key: string]: unknown;
};

type LayerId = "hvi" | "plantability" | "ndvi_change";

const MUMBAI_CENTER: [number, number] = [19.076, 72.877];

// Sequential ramp (ColorBrewer YlOrRd, colorblind-safe) — low HVI (cooler/safer)
// to high HVI (hotter/more vulnerable).
const HVI_COLORS = ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"];

function colorForHvi(hvi: number | null): string {
  if (hvi === null || Number.isNaN(hvi)) return "#cccccc";
  const bins = [20, 35, 50, 65, 80];
  const idx = bins.findIndex((b) => hvi < b);
  return idx === -1 ? HVI_COLORS[HVI_COLORS.length - 1] : HVI_COLORS[idx];
}

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
          <div className="flex overflow-hidden rounded-sm">
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
              <span className="h-3 w-3 rounded-sm" style={{ background: "#4ade80" }} />
              <span>Yes, suitable for planting</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: "#f87171" }} />
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
              <span className="h-3 w-3 rounded-sm" style={{ background: "#4ade80" }} />
              <span>Gained vegetation</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm border border-border" style={{ background: "#d4d4d8" }} />
              <span>Stable</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-sm" style={{ background: "#f87171" }} />
              <span>Lost vegetation</span>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}

/** Flattens any GeoJSON Polygon/MultiPolygon ring nesting down to raw [lng,lat] pairs. */
function flattenPositions(coords: unknown): Position[] {
  if (!Array.isArray(coords)) return [];
  if (typeof coords[0] === "number") return [coords as Position];
  return (coords as unknown[]).flatMap(flattenPositions);
}

function boundsOf(geometry: Geometry): LatLngBoundsExpression | null {
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
      map.fitBounds(bounds, { padding: [24, 24] });
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
  const [nbsRecs, setNbsRecs] = useState<NbsRec[]>([]);

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

  useEffect(() => {
    fetch("/nbs_recommendations.json")
      .then((res) => res.json())
      .then(setNbsRecs)
      .catch(() => setNbsRecs([]));
  }, []);

  const data = cache[activeLayer];
  const wardsGeo = (cache.hvi as FeatureCollection<Geometry, WardProps> | undefined) ?? null;

  // Only isFullscreen forces a remount (it needs onEachFeature to rebind
  // popups). Selection changes restyle the already-mounted layer in place via
  // the ref below — remounting on every ward click would tear down and
  // recreate the layer mid-click, which silently kills any popup Leaflet was
  // about to open on that same click.
  const layerRef = useRef<LeafletGeoJSONLayer | null>(null);
  useEffect(() => {
    if (!layerRef.current) return;
    if (activeLayer === "hvi") layerRef.current.setStyle(styleHvi(selectedWardId) as (f?: Feature<Geometry>) => PathOptions);
    else if (activeLayer === "plantability")
      layerRef.current.setStyle(stylePlantability(selectedWardId) as (f?: Feature<Geometry>) => PathOptions);
    else layerRef.current.setStyle(styleNdviChange(selectedWardId) as (f?: Feature<Geometry>) => PathOptions);
  }, [selectedWardId, activeLayer]);

  /** Ward summary + top cited intervention (with source and year), for the
   *  fullscreen popup — fullscreen hides the sidebar detail panel, so this is
   *  the only place that information is otherwise reachable from there. */
  function popupHtml(wardId: string): string {
    const p = wardsGeo?.features.find((f) => f.properties.ward_id === wardId)?.properties;
    const areas = areasForWard(wardId);
    const rec = nbsRecs.filter((r) => r.ward_id === wardId).sort((a, b) => a.priority - b.priority)[0];
    const cited = rec ? matchCitationFromText(rec.citation) : undefined;

    const hviLine = p
      ? `<div style="font-size:12px;color:#52525b;margin-top:2px;">HVI ${p.HVI !== null ? p.HVI.toFixed(1) : "n/a"} &middot; priority ${p.rank ?? "n/a"} of 24</div>`
      : "";
    const areasLine = areas.length
      ? `<div style="font-size:11px;color:#71717a;margin-top:4px;">${areas.join(", ")}</div>`
      : "";
    const sourceHtml = cited
      ? `<a href="https://doi.org/${cited.doi}" target="_blank" rel="noopener noreferrer" style="color:#0EA5B3;">${cited.authors}</a> &middot; ${cited.year}`
      : rec
        ? `<span style="font-style:italic;">${rec.citation}</span>`
        : "";
    const recBlock = rec
      ? `<div style="margin-top:8px;padding-top:8px;border-top:1px solid #e4e4e7;">
           <div style="font-size:12px;font-weight:600;color:#18181b;">${rec.intervention}</div>
           <div style="font-size:11px;color:#52525b;margin-top:2px;">${rec.rationale}</div>
           <div style="font-size:11px;color:#71717a;margin-top:4px;">${sourceHtml}</div>
         </div>`
      : "";

    return `<div style="min-width:200px;"><div style="font-size:14px;font-weight:700;color:#18181b;">Ward ${wardId}</div>${hviLine}${areasLine}${recBlock}</div>`;
  }

  function selectFrom<P extends { ward_id: string }>(feature: Feature<Geometry, P>, layer: Layer) {
    const wardId = feature.properties.ward_id;
    layer.on("click", () => onSelectWard?.(wardId));
    if (isFullscreen) {
      layer.bindPopup(popupHtml(wardId));
    }
  }

  return (
    <div className="absolute inset-0">
      <Card className="absolute right-2 top-2 z-[1000] w-fit gap-0 bg-background/95 p-1.5 backdrop-blur-sm">
        <div className="flex items-center gap-1">
          <Tabs value={activeLayer} onValueChange={(v: string) => setActiveLayer(v as LayerId)}>
            <TabsList aria-label="Map layer">
              {(Object.keys(LAYER_META) as LayerId[]).map((id) => (
                <TabsTrigger
                  key={id}
                  value={id}
                  title={LAYER_META[id].caption}
                  className="whitespace-nowrap px-2"
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

      <MapContainer center={MUMBAI_CENTER} zoom={11} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {data && activeLayer === "hvi" && (
          <GeoJSON
            key={`hvi-${isFullscreen}`}
            ref={layerRef}
            data={data as FeatureCollection<Geometry, WardProps>}
            style={styleHvi(selectedWardId) as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "plantability" && (
          <GeoJSON
            key={`plantability-${isFullscreen}`}
            ref={layerRef}
            data={data as FeatureCollection<Geometry, CellNbsProps>}
            style={stylePlantability(selectedWardId) as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "ndvi_change" && (
          <GeoJSON
            key={`ndvi_change-${isFullscreen}`}
            ref={layerRef}
            data={data as FeatureCollection<Geometry, CellNdviProps>}
            style={styleNdviChange(selectedWardId) as (f?: Feature<Geometry>) => PathOptions}
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
