/**
 * GET /api/v1/export?dataset=&format=
 *
 * The whole dataset in one cached call (issue #105).
 *
 * Without this, the considerate way to use the API was also the slowest one:
 * anyone wanting everything had to page through /cells 541 rows at a time, so
 * the polite user hammered the API and the impatient one hammered it harder.
 * The docs already told people not to poll and to take the dataset in one
 * request; this is the request they were told to make.
 *
 * Served from the committed snapshots, never from the database, and that is
 * deliberate rather than a fallback. A bulk export is by definition the
 * complete published dataset, the snapshots are exactly that, and routing the
 * heaviest response in the API around the free-tier database keeps it out of
 * the request path for the traffic most likely to overwhelm it.
 *
 * CSV is a first-class format here, not a courtesy. The research audience for
 * this data works in pandas and R, where a FeatureCollection of 541 polygons is
 * the wrong shape, and the cell centre as plain lon/lat columns is what lets
 * someone plot it without a geometry library.
 */

import type { Feature, FeatureCollection, Geometry } from "geojson";
import {
  CACHE_HEADER,
  errorResponse,
  jsonResponse,
  optionsResponse,
  readSnapshot,
  rateLimited,
} from "../_lib";

export const revalidate = 3600;

type Props = Record<string, unknown>;

const DATASETS = {
  cells: {
    snapshot: "cells_nbs.geojson",
    // Merged in from a second snapshot, the two columns it actually adds.
    // Carrying every column from both would ship the same indicator twice
    // under two names and invite someone to analyse the wrong one.
    extraSnapshot: "cells_ndvi_change.geojson",
    extraColumns: ["ndvi_delta", "change_class"],
    joinKey: "grid_id",
    filename: "ucip_cells",
  },
  wards: {
    snapshot: "wards_hvi.geojson",
    extraSnapshot: null,
    extraColumns: [] as string[],
    joinKey: "ward_id",
    filename: "ucip_wards",
  },
} as const;

type DatasetName = keyof typeof DATASETS;

const FORMATS = ["geojson", "csv"] as const;
type Format = (typeof FORMATS)[number];

function isDataset(value: string): value is DatasetName {
  return value in DATASETS;
}

function isFormat(value: string): value is Format {
  return (FORMATS as readonly string[]).includes(value);
}

/**
 * Centre of a feature, as the mean of its exterior ring vertices.
 *
 * The cells are axis-aligned squares built in projected metres and reprojected,
 * so for that geometry this and the true centroid agree to well under a metre.
 * Ward polygons are irregular, so their centre is a rough label point rather
 * than a centroid, which is why the CSV header says so.
 */
function ringCentre(geometry: Geometry | null): { lon: number; lat: number } | null {
  if (!geometry) return null;

  let ring: unknown;
  if (geometry.type === "Polygon") ring = geometry.coordinates[0];
  else if (geometry.type === "MultiPolygon") ring = geometry.coordinates[0]?.[0];
  else return null;

  if (!Array.isArray(ring) || ring.length === 0) return null;

  let points = ring as [number, number][];
  // A closed ring repeats its first vertex, which would weight that corner twice.
  const first = points[0];
  const last = points[points.length - 1];
  if (points.length > 1 && first[0] === last[0] && first[1] === last[1]) {
    points = points.slice(0, -1);
  }

  const n = points.length;
  if (n === 0) return null;

  return {
    lon: Number((points.reduce((sum, p) => sum + p[0], 0) / n).toFixed(6)),
    lat: Number((points.reduce((sum, p) => sum + p[1], 0) / n).toFixed(6)),
  };
}

/** RFC 4180 quoting: only when needed, and doubling any embedded quote. */
function csvCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function toCsv(rows: Props[]): string {
  if (rows.length === 0) return "";

  // Union of keys rather than the first row's, so a field absent from row one
  // is not silently dropped from the whole export.
  const columns: string[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        columns.push(key);
      }
    }
  }

  const lines = [columns.join(",")];
  for (const row of rows) {
    lines.push(columns.map((column) => csvCell(row[column])).join(","));
  }
  // Trailing newline: POSIX text convention, and some CSV readers want it.
  return `${lines.join("\n")}\n`;
}

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const limited = await rateLimited(request);
  if (limited) return limited;

  const url = new URL(request.url);

  const rawDataset = (url.searchParams.get("dataset") ?? "cells").toLowerCase();
  if (!isDataset(rawDataset)) {
    return errorResponse(
      400,
      `'${rawDataset}' is not a dataset.`,
      `Try one of: ${Object.keys(DATASETS).join(", ")}`
    );
  }

  const rawFormat = (url.searchParams.get("format") ?? "geojson").toLowerCase();
  if (!isFormat(rawFormat)) {
    return errorResponse(
      400,
      `'${rawFormat}' is not a format.`,
      `Try one of: ${FORMATS.join(", ")}`
    );
  }

  const spec = DATASETS[rawDataset];
  const geo = await readSnapshot<FeatureCollection<Geometry, Props>>(spec.snapshot);

  let extras: Map<unknown, Props> | null = null;
  if (spec.extraSnapshot) {
    const extraGeo = await readSnapshot<FeatureCollection<Geometry, Props>>(spec.extraSnapshot);
    extras = new Map(
      extraGeo.features.map((f) => [f.properties?.[spec.joinKey], f.properties ?? {}])
    );
  }

  const withExtras = (feature: Feature<Geometry, Props>): Props => {
    const props: Props = { ...(feature.properties ?? {}) };
    const extra = extras?.get(props[spec.joinKey]);
    for (const column of spec.extraColumns) {
      props[column] = extra ? extra[column] ?? null : null;
    }
    return props;
  };

  if (rawFormat === "geojson") {
    const body: FeatureCollection<Geometry, Props> = {
      type: "FeatureCollection",
      features: geo.features.map((feature) => ({
        ...feature,
        properties: withExtras(feature),
      })),
    };
    return jsonResponse(body, {
      headers: {
        "content-disposition": `inline; filename="${spec.filename}.geojson"`,
      },
    });
  }

  const rows = geo.features.map((feature) => {
    const centre = ringCentre(feature.geometry);
    // Identity first, then position, then everything measured. A CSV opened in
    // a spreadsheet is read left to right by a human.
    return {
      [spec.joinKey]: feature.properties?.[spec.joinKey] ?? null,
      lon: centre?.lon ?? null,
      lat: centre?.lat ?? null,
      ...withExtras(feature),
    } as Props;
  });

  return new Response(toCsv(rows), {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": `attachment; filename="${spec.filename}.csv"`,
      "cache-control": CACHE_HEADER,
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, OPTIONS",
    },
  });
}
