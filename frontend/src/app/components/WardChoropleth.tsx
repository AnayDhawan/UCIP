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

function styleWard(feature?: Feature<Geometry, WardProps>): PathOptions {
  const hvi = feature?.properties?.HVI ?? null;
  return {
    fillColor: colorForHvi(hvi),
    fillOpacity: 0.75,
    color: "#333333",
    weight: 1,
  };
}

function onEachWard(feature: Feature<Geometry, WardProps>, layer: Layer) {
  const p = feature.properties;
  const hvi = p.HVI !== null ? p.HVI.toFixed(1) : "n/a";
  const rank = p.rank !== null ? p.rank : "n/a";
  layer.bindPopup(
    `<strong>Ward ${p.ward_id}</strong><br/>` +
      `HVI: ${hvi} / 100<br/>` +
      `Priority rank: ${rank} of 24<br/>` +
      `Grid cells: ${p.n_cells ?? "n/a"}`
  );
}

export default function WardChoropleth() {
  const [data, setData] = useState<FeatureCollection<Geometry, WardProps> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/wards_hvi.geojson")
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then(setData)
      .catch((err) => setError(String(err)));
  }, []);

  if (error) {
    return <div className="absolute inset-0 p-8 text-red-600">Failed to load ward data: {error}</div>;
  }
  if (!data) {
    return <div className="absolute inset-0 p-8 text-zinc-500">Loading Mumbai ward HVI map…</div>;
  }

  // Absolute inset-0 (rather than height:100%) sidesteps a flex/percentage-height
  // quirk where Leaflet's container resolves to 0px height inside a flex-grow chain.
  return (
    <div className="absolute inset-0">
      <MapContainer center={MUMBAI_CENTER} zoom={11} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON data={data} style={styleWard} onEachFeature={onEachWard} />
      </MapContainer>
    </div>
  );
}
