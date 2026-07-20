"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection, Geometry, Position } from "geojson";
import type { LatLngBoundsExpression, Layer, PathOptions } from "leaflet";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

export default function WardChoropleth({
  selectedWardId = null,
  onSelectWard,
}: {
  selectedWardId?: string | null;
  onSelectWard?: (wardId: string) => void;
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

  function selectFrom<P extends { ward_id: string }>(feature: Feature<Geometry, P>, layer: Layer) {
    layer.on("click", () => onSelectWard?.(feature.properties.ward_id));
  }

  return (
    <div className="absolute inset-0">
      <Card className="absolute right-2 top-2 z-[1000] w-fit max-w-[360px] gap-0 bg-background/95 p-1.5 backdrop-blur-sm">
        <Tabs value={activeLayer} onValueChange={(v: string) => setActiveLayer(v as LayerId)}>
          <TabsList aria-label="Map layer" className="w-full">
            {(Object.keys(LAYER_META) as LayerId[]).map((id) => (
              <TabsTrigger key={id} value={id} className="whitespace-nowrap px-2">
                {LAYER_META[id].label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <p className="px-1 pb-0.5 pt-1.5 text-[11px] leading-snug text-muted-foreground">
          {LAYER_META[activeLayer].caption}
        </p>
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
            key={`hvi-${selectedWardId ?? "none"}`}
            data={data as FeatureCollection<Geometry, WardProps>}
            style={styleHvi(selectedWardId) as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "plantability" && (
          <GeoJSON
            key={`plantability-${selectedWardId ?? "none"}`}
            data={data as FeatureCollection<Geometry, CellNbsProps>}
            style={stylePlantability(selectedWardId) as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "ndvi_change" && (
          <GeoJSON
            key={`ndvi_change-${selectedWardId ?? "none"}`}
            data={data as FeatureCollection<Geometry, CellNdviProps>}
            style={styleNdviChange(selectedWardId) as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={selectFrom as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        <FlyToSelection selectedWardId={selectedWardId} wardsGeo={wardsGeo} />
      </MapContainer>
    </div>
  );
}
