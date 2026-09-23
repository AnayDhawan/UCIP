import { notFound } from "next/navigation";
import type { FeatureCollection, Geometry } from "geojson";
import Link from "next/link";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { hviColor } from "@/lib/hvi";
import type { WardProps } from "@/lib/wardTypes";

const wards = JSON.parse(
  readFileSync(join(process.cwd(), "public", "wards_hvi.geojson"), "utf8")
) as FeatureCollection<Geometry, WardProps>;

export function generateStaticParams() {
  return wards.features.map(({ properties }) => ({ wardId: properties.ward_id }));
}

export const dynamicParams = false;

export default async function WardEmbed({ params }: { params: Promise<{ wardId: string }> }) {
  const { wardId } = await params;
  const ward = wards.features.find(({ properties }) => properties.ward_id === wardId.toUpperCase());
  if (!ward) notFound();
  const { HVI, rank, n_cells, ward_id } = ward.properties;

  return (
    <main className="embed-card">
      <p className="embed-kicker">UCIP · Mumbai heat vulnerability</p>
      <div className="embed-title-row">
        <h1>Ward {ward_id}</h1>
        <span className="embed-score" style={{ background: hviColor(HVI) }}>{HVI?.toFixed(1) ?? "n/a"}</span>
      </div>
      <p>Priority {rank ?? "n/a"} of 24 · {n_cells ?? "n/a"} grid cells</p>
      <Link href={`/dashboard?ward=${encodeURIComponent(ward_id)}`} target="_blank" rel="noopener noreferrer">
        Open full ward brief →
      </Link>
    </main>
  );
}
