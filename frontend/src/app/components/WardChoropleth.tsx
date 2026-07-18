"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { Layer, PathOptions } from "leaflet";

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

function styleHvi(feature?: Feature<Geometry, WardProps>): PathOptions {
  return {
    fillColor: colorForHvi(feature?.properties?.HVI ?? null),
    fillOpacity: 0.75,
    color: "#333333",
    weight: 1,
  };
}

function onEachHvi(feature: Feature<Geometry, WardProps>, layer: Layer) {
  const p = feature.properties;
  layer.bindPopup(
    `<strong>Ward ${p.ward_id}</strong><br/>` +
      `HVI: ${p.HVI !== null ? p.HVI.toFixed(1) : "n/a"} / 100<br/>` +
      `Priority rank: ${p.rank ?? "n/a"} of 24<br/>` +
      `Grid cells: ${p.n_cells ?? "n/a"}`
  );
}

function stylePlantability(feature?: Feature<Geometry, CellNbsProps>): PathOptions {
  const plantable = feature?.properties?.plantable;
  return {
    fillColor: plantable ? "#4ade80" : "#f87171",
    fillOpacity: 0.65,
    color: "#333333",
    weight: 0.5,
  };
}

function onEachPlantability(feature: Feature<Geometry, CellNbsProps>, layer: Layer) {
  const p = feature.properties;
  layer.bindPopup(
    `<strong>Cell ${p.grid_id}</strong> (Ward ${p.ward_id})<br/>` +
      `Plantable: ${p.plantable ? "yes" : "no, rejected for afforestation"}<br/>` +
      `WorldCover class: ${p.worldcover_class ?? "n/a"}<br/>` +
      `NBS rule fired: ${p.nbs_fired ? "yes" : "no"}`
  );
}

const NDVI_CHANGE_COLORS: Record<string, string> = {
  gained: "#4ade80",
  stable: "#d4d4d8",
  lost: "#f87171",
  unknown: "#e5e5e5",
};

function styleNdviChange(feature?: Feature<Geometry, CellNdviProps>): PathOptions {
  const cls = feature?.properties?.change_class ?? "unknown";
  return {
    fillColor: NDVI_CHANGE_COLORS[cls] ?? "#e5e5e5",
    fillOpacity: 0.7,
    color: "#333333",
    weight: 0.5,
  };
}

function onEachNdviChange(feature: Feature<Geometry, CellNdviProps>, layer: Layer) {
  const p = feature.properties;
  layer.bindPopup(
    `<strong>Cell ${p.grid_id}</strong> (Ward ${p.ward_id})<br/>` +
      `Green cover: ${p.change_class}<br/>` +
      `NDVI delta: ${p.ndvi_delta !== null ? p.ndvi_delta.toFixed(3) : "n/a"}`
  );
}

const LAYER_META: Record<LayerId, { label: string; url: string }> = {
  hvi: { label: "HVI", url: "/wards_hvi.geojson" },
  plantability: { label: "Plantability", url: "/cells_nbs.geojson" },
  ndvi_change: { label: "Green-cover change", url: "/cells_ndvi_change.geojson" },
};

export default function WardChoropleth() {
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

  return (
    <div className="absolute inset-0">
      <div className="absolute right-2 top-2 z-[1000] flex gap-1 rounded bg-white p-1 shadow dark:bg-zinc-900">
        {(Object.keys(LAYER_META) as LayerId[]).map((id) => (
          <button
            key={id}
            onClick={() => setActiveLayer(id)}
            className={`rounded px-2 py-1 text-xs font-medium ${
              activeLayer === id
                ? "bg-zinc-800 text-white dark:bg-zinc-200 dark:text-black"
                : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
            }`}
          >
            {LAYER_META[id].label}
          </button>
        ))}
      </div>

      {error && (
        <div className="absolute inset-x-0 top-12 z-[1000] mx-auto w-fit rounded bg-red-100 px-3 py-1 text-sm text-red-700">
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
            key="hvi"
            data={data as FeatureCollection<Geometry, WardProps>}
            style={styleHvi as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={onEachHvi as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "plantability" && (
          <GeoJSON
            key="plantability"
            data={data as FeatureCollection<Geometry, CellNbsProps>}
            style={stylePlantability as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={onEachPlantability as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
        {data && activeLayer === "ndvi_change" && (
          <GeoJSON
            key="ndvi_change"
            data={data as FeatureCollection<Geometry, CellNdviProps>}
            style={styleNdviChange as (f?: Feature<Geometry>) => PathOptions}
            onEachFeature={onEachNdviChange as (f: Feature<Geometry>, l: Layer) => void}
          />
        )}
      </MapContainer>
    </div>
  );
}
