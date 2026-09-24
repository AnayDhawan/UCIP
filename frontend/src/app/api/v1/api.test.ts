/**
 * Tests for the public v1 API (issue #70).
 *
 * These exercise the route handlers directly rather than over HTTP, so they run
 * in CI with no server and no Supabase credentials. That is also the path worth
 * testing hardest: with no database configured, every route falls back to the
 * committed snapshots, which is exactly what a fresh clone and a database
 * outage both look like.
 *
 * The lookup expectations were cross-checked against shapely's own
 * point-in-polygon over the same GeoJSON, so they pin correctness rather than
 * just current behaviour.
 */

import { describe, it, expect, beforeAll } from "vitest";
import { GET as getMeta } from "./meta/route";
import { GET as getWards } from "./wards/route";
import { GET as getWard } from "./wards/[wardId]/route";
import { GET as getLookup } from "./lookup/route";
import { GET as getRecs } from "./recommendations/route";
import { GET as getCells, CELL_FIELDS } from "./cells/route";
import { GET as getSpec } from "./openapi.json/route";
import { GET as getExport } from "./export/route";

const BASE = "https://uciplatform.vercel.app";

beforeAll(() => {
  // Force the snapshot path: no database configured. Both name pairs have to go,
  // since supabase() falls back from the unprefixed to the NEXT_PUBLIC_ names.
  delete process.env.SUPABASE_URL;
  delete process.env.SUPABASE_ANON_KEY;
  delete process.env.NEXT_PUBLIC_SUPABASE_URL;
  delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
});

/**
 * Parsed JSON, walked structurally. These tests read an OpenAPI document by
 * path, which is exactly the case `any` exists for; modelling the spec as a
 * type here would be a second copy of it to keep in sync.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;

/** Walks a chain of keys, returning undefined rather than throwing part-way. */
const get = (node: Json, ...keys: string[]): Json =>
  keys.reduce((acc, key) => (acc == null ? acc : acc[key]), node);

const req = (path: string) => new Request(`${BASE}${path}`);
const body = async (res: Response) => JSON.parse(await res.text());

describe("GET /api/v1/meta", () => {
  it("reports coverage, counts and method", async () => {
    const res = await getMeta(req("/api/v1/meta"));
    expect(res.status).toBe(200);
    const json = await body(res);
    expect(json.counts.wards).toBe(24);
    expect(json.counts.citations).toBeGreaterThan(0);
    expect(json.license.code).toBe("Apache-2.0");
  });

  it("nulls the data-vintage fields until a committed run log exists", async () => {
    const json = await body(await getMeta(req("/api/v1/meta")));
    // The repo has no committed pipeline_run_log.json yet, so the endpoint must
    // not invent a refresh date. This is the honest answer until the first
    // refresh run commits one.
    expect(json.generated_at).toBeNull();
    expect(json.composite_window).toBeNull();
  });

  it("reports the refresh date and composite window from the run log", async () => {
    const fs = await import("node:fs/promises");
    const path = await import("node:path");
    const logPath = path.join(process.cwd(), "public", "pipeline_run_log.json");
    try {
      await fs.writeFile(
        logPath,
        JSON.stringify({
          started_at: "2026-09-03T04:00:00+00:00",
          finished_at: "2026-09-03T05:30:00+00:00",
          composite_window: { start: "2025-11-01", end: "2026-02-28" },
          stages: [],
        })
      );
      const json = await body(await getMeta(req("/api/v1/meta")));
      expect(json.generated_at).toBe("2026-09-03T05:30:00+00:00");
      expect(json.composite_window).toEqual({
        start: "2025-11-01",
        end: "2026-02-28",
      });
    } finally {
      await fs.rm(logPath, { force: true });
    }
  });
});

describe("GET /api/v1/wards", () => {
  it("returns all 24 wards ranked most vulnerable first", async () => {
    const res = await getWards(req("/api/v1/wards"));
    expect(res.status).toBe(200);
    const json = await body(res);
    expect(json.wards).toHaveLength(24);
    expect(json.wards[0].rank).toBe(1);
    const ranks = json.wards.map((w: { rank: number }) => w.rank);
    expect([...ranks].sort((a, b) => a - b)).toEqual(ranks);
  });

  it("honours limit", async () => {
    const json = await body(await getWards(req("/api/v1/wards?limit=3")));
    expect(json.wards).toHaveLength(3);
  });

  it("caps limit at the number of wards that exist", async () => {
    const json = await body(await getWards(req("/api/v1/wards?limit=9999")));
    expect(json.wards).toHaveLength(24);
  });

  it("omits geometry unless asked", async () => {
    const plain = await body(await getWards(req("/api/v1/wards?limit=1")));
    expect(plain.wards[0].geom_geojson).toBeUndefined();
    const withGeom = await body(await getWards(req("/api/v1/wards?limit=1&geometry=true")));
    expect(withGeom.wards[0].geom_geojson).toBeDefined();
  });

  it("exposes the factor breakdown, which is the explainability claim", async () => {
    const json = await body(await getWards(req("/api/v1/wards?limit=1")));
    expect(Object.keys(json.wards[0].contrib).length).toBeGreaterThan(0);
  });

  it("sets an open CORS header and a cache header", async () => {
    const res = await getWards(req("/api/v1/wards?limit=1"));
    expect(res.headers.get("access-control-allow-origin")).toBe("*");
    expect(res.headers.get("cache-control")).toContain("s-maxage");
  });
});

describe("GET /api/v1/wards/{wardId}", () => {
  const call = (id: string) =>
    getWard(req(`/api/v1/wards/${id}`), { params: Promise.resolve({ wardId: id }) });

  it("returns a ward with its ranked recommendations", async () => {
    const json = await body(await call("C"));
    expect(json.ward.ward_id).toBe("C");
    expect(json.ward.rank).toBe(1);
    expect(json.recommendations.length).toBeGreaterThan(0);
    const priorities = json.recommendations.map((r: { priority: number }) => r.priority);
    expect([...priorities].sort((a, b) => a - b)).toEqual(priorities);
  });

  it("resolves a URL-encoded split ward code", async () => {
    const json = await body(await call("F%2FN"));
    expect(json.ward.ward_id).toBe("F/N");
  });

  it("accepts a lowercase code", async () => {
    const json = await body(await call("f%2Fn"));
    expect(json.ward.ward_id).toBe("F/N");
  });

  it("400s on a malformed code rather than querying with it", async () => {
    expect((await call("ZZZZZ")).status).toBe(400);
    expect((await call("%3Cscript%3E")).status).toBe(400);
    expect((await call("..%2F..%2Fetc")).status).toBe(400);
  });

  it("404s on a well-formed code that does not exist", async () => {
    // "ZZ" is shaped like a ward code but is not one of the 24.
    expect((await call("ZZ")).status).toBe(404);
  });

  it("every recommendation carries a citation", async () => {
    const json = await body(await call("C"));
    for (const rec of json.recommendations) {
      expect(rec.citation.trim()).not.toBe("");
      expect(rec.rationale.trim()).not.toBe("");
    }
  });
});

describe("GET /api/v1/lookup", () => {
  it("resolves a coordinate to the ward that contains it", async () => {
    // Cross-checked against shapely over the same GeoJSON.
    const json = await body(await getLookup(req("/api/v1/lookup?lat=19.076&lon=72.877")));
    expect(json.ward.ward_id).toBe("L");
    expect(json.query).toEqual({ lat: 19.076, lon: 72.877 });
  });

  it("resolves a second, independently checked coordinate", async () => {
    const json = await body(await getLookup(req("/api/v1/lookup?lat=19.0176&lon=72.8562")));
    expect(json.ward.ward_id).toBe("F/N");
  });

  it("404s for a point outside every ward", async () => {
    // Null Island, and a point just outside Mumbai's north-east edge.
    expect((await getLookup(req("/api/v1/lookup?lat=0&lon=0"))).status).toBe(404);
    expect((await getLookup(req("/api/v1/lookup?lat=19.2183&lon=72.9781"))).status).toBe(404);
  });

  it("400s on missing or unparseable coordinates", async () => {
    expect((await getLookup(req("/api/v1/lookup"))).status).toBe(400);
    expect((await getLookup(req("/api/v1/lookup?lat=19.076"))).status).toBe(400);
    expect((await getLookup(req("/api/v1/lookup?lat=abc&lon=72.8"))).status).toBe(400);
  });

  it("400s on coordinates outside the valid range", async () => {
    expect((await getLookup(req("/api/v1/lookup?lat=91&lon=0"))).status).toBe(400);
    expect((await getLookup(req("/api/v1/lookup?lat=0&lon=181"))).status).toBe(400);
  });

  it("attaches the ward's highest-priority recommendation", async () => {
    const json = await body(await getLookup(req("/api/v1/lookup?lat=19.076&lon=72.877")));
    expect(json.top_recommendation.priority).toBe(1);
    expect(json.top_recommendation.citation).toBeTruthy();
  });
});

describe("GET /api/v1/recommendations", () => {
  it("returns all recommendations", async () => {
    const json = await body(await getRecs(req("/api/v1/recommendations")));
    expect(json.count).toBeGreaterThan(0);
  });

  it("filters by ward", async () => {
    const json = await body(await getRecs(req("/api/v1/recommendations?ward=C")));
    expect(json.recommendations.every((r: { ward_id: string }) => r.ward_id === "C")).toBe(true);
  });

  it("400s on a malformed ward filter", async () => {
    expect((await getRecs(req("/api/v1/recommendations?ward=%3Cscript%3E"))).status).toBe(400);
  });

  it("has no duplicate rows, the bug fixed in ed1e335", async () => {
    // The Supabase table held every recommendation twice because an identity
    // primary key gave upsert nothing to conflict on. The snapshot is the
    // pipeline's own output and must never show the same problem.
    const json = await body(await getRecs(req("/api/v1/recommendations?limit=500")));
    const keys = json.recommendations.map(
      (r: { ward_id: string; intervention: string; priority: number }) =>
        `${r.ward_id}|${r.intervention}|${r.priority}`
    );
    expect(new Set(keys).size).toBe(keys.length);
  });
});

describe("GET /api/v1/cells", () => {
  it("returns the analysis grid", async () => {
    const json = await body(await getCells(req("/api/v1/cells")));
    expect(json.count).toBeGreaterThan(0);
  });

  it("filters by ward", async () => {
    const json = await body(await getCells(req("/api/v1/cells?ward=C")));
    expect(json.cells.every((c: { ward_id: string }) => c.ward_id === "C")).toBe(true);
  });

  it("filters by bbox", async () => {
    const all = await body(await getCells(req("/api/v1/cells")));
    const boxed = await body(await getCells(req("/api/v1/cells?bbox=72.80,19.00,72.90,19.10")));
    expect(boxed.count).toBeGreaterThan(0);
    expect(boxed.count).toBeLessThan(all.count);
  });

  it("400s on a malformed bbox", async () => {
    expect((await getCells(req("/api/v1/cells?bbox=bad"))).status).toBe(400);
    expect((await getCells(req("/api/v1/cells?bbox=1,2,3"))).status).toBe(400);
    // Inverted box: min greater than max.
    expect((await getCells(req("/api/v1/cells?bbox=73,19.2,72.8,19"))).status).toBe(400);
  });

  it("omits geometry unless asked", async () => {
    const json = await body(await getCells(req("/api/v1/cells?ward=C")));
    expect(json.cells[0].geom_geojson).toBeUndefined();
  });

  // These tests exist because the two sources disagreed. The database path
  // selected CELL_FIELDS; the snapshot path spread the raw GeoJSON properties,
  // so the same endpoint answered with `hvi` or `HVI`, and a different key set,
  // depending on whether Supabase was reachable. A generated client typed on
  // one shape broke on the other, on the fallback path specifically.
  it("returns exactly the documented fields, whichever source answered", async () => {
    const json = await body(await getCells(req("/api/v1/cells?ward=C")));
    expect(Object.keys(json.cells[0]).sort()).toEqual([...CELL_FIELDS].sort());
  });

  it("publishes no SCREAMING snapshot keys and no pipeline internals", async () => {
    const json = await body(await getCells(req("/api/v1/cells?ward=C")));
    const keys = Object.keys(json.cells[0]);
    for (const leaked of ["HVI", "LST_C", "NDVI", "NDVI_prev", "ward_gid", "nbs_fired", "dist_to_water_m"]) {
      expect(keys, `${leaked} leaked from the snapshot`).not.toContain(leaked);
    }
    // The contrib_* fields are ward-level and belong to /wards, not here.
    expect(keys.filter((k) => k.startsWith("contrib_"))).toEqual([]);
  });

  it("types plantable as a boolean rather than the snapshot's 0/1", async () => {
    const json = await body(await getCells(req("/api/v1/cells?ward=C")));
    for (const cell of json.cells) {
      expect(cell.plantable === null || typeof cell.plantable === "boolean").toBe(true);
    }
  });
});

describe("GET /api/v1/openapi.json", () => {
  it("describes every implemented path", async () => {
    const json = await body(await getSpec(req("/api/v1/openapi.json")));
    expect(json.openapi).toBe("3.1.0");
    for (const path of [
      "/meta",
      "/wards",
      "/wards/{wardId}",
      "/lookup",
      "/recommendations",
      "/cells",
      "/export",
    ]) {
      expect(json.paths[path], `spec is missing ${path}`).toBeDefined();
    }
  });

  it("points its server URL at the requesting origin", async () => {
    const json = await body(await getSpec(req("/api/v1/openapi.json")));
    expect(json.servers[0].url).toBe(`${BASE}/api/v1`);
  });

  it("gives every 200 a schema, not just a description", async () => {
    // A response documented as prose is useless to a generator: the client type
    // comes out as `unknown`. This is the check that keeps the spec generatable.
    const spec = await body(await getSpec(req("/api/v1/openapi.json")));
    for (const [path, item] of Object.entries(spec.paths as Record<string, Json>)) {
      const ok = get(item, "get", "responses", "200");
      expect(ok?.content, `${path} 200 has no content schema`).toBeDefined();
      const firstMediaType = Object.values(ok!.content as Record<string, Json>)[0];
      expect(firstMediaType?.schema, `${path} 200 content has no schema`).toBeDefined();
    }
  });

  it("resolves every $ref it uses", async () => {
    const spec = await body(await getSpec(req("/api/v1/openapi.json")));
    const refs = new Set<string>();
    const walk = (node: unknown) => {
      if (Array.isArray(node)) return node.forEach(walk);
      if (node && typeof node === "object") {
        for (const [k, v] of Object.entries(node)) {
          if (k === "$ref" && typeof v === "string") refs.add(v);
          else walk(v);
        }
      }
    };
    walk(spec.paths);
    walk(spec.components);
    expect(refs.size).toBeGreaterThan(0);
    for (const r of refs) {
      const name = r.replace("#/components/schemas/", "");
      expect(spec.components.schemas[name], `dangling $ref ${r}`).toBeDefined();
    }
  });
});

/**
 * The spec is only worth generating clients from if it describes what the API
 * actually returns. These walk real responses against the declared schemas in
 * both directions: a documented required field that is missing, and a returned
 * field that is undocumented. The second direction is the one that rots
 * quietly, because adding a field to a handler breaks nothing until somebody
 * generates a client and finds it absent.
 */
describe("the spec matches what the routes return", () => {
  let spec: Json;

  beforeAll(async () => {
    spec = await body(await getSpec(req("/api/v1/openapi.json")));
  });

  const schemaNamed = (name: string): Json =>
    (spec.components as Json).schemas[name] as Json;

  const resolve = (schema: Json): Json =>
    typeof schema?.$ref === "string"
      ? resolve(schemaNamed(schema.$ref.replace("#/components/schemas/", "")))
      : schema;

  /** Asserts an object carries every required key and no undeclared ones. */
  function check(value: Record<string, unknown>, schemaName: string, where: string) {
    const schema = resolve(schemaNamed(schemaName));
    const declared = Object.keys((schema.properties ?? {}) as object);
    for (const required of (schema.required ?? []) as string[]) {
      expect(value, `${where}: missing required ${required}`).toHaveProperty(required);
    }
    for (const key of Object.keys(value)) {
      expect(declared, `${where}: '${key}' is returned but undocumented`).toContain(key);
    }
  }

  it("Ward", async () => {
    const json = await body(await getWards(req("/api/v1/wards?limit=2")));
    check(json.wards[0], "Ward", "/wards");
    const withGeom = await body(await getWards(req("/api/v1/wards?limit=1&geometry=true")));
    check(withGeom.wards[0], "Ward", "/wards?geometry=true");
  });

  it("Cell", async () => {
    const json = await body(await getCells(req("/api/v1/cells?limit=2")));
    check(json.cells[0], "Cell", "/cells");
    const withGeom = await body(await getCells(req("/api/v1/cells?limit=1&geometry=true")));
    check(withGeom.cells[0], "Cell", "/cells?geometry=true");
  });

  it("Recommendation", async () => {
    const json = await body(await getRecs(req("/api/v1/recommendations?limit=2")));
    check(json.recommendations[0], "Recommendation", "/recommendations");
  });

  it("Meta", async () => {
    check(await body(await getMeta(req("/api/v1/meta"))), "Meta", "/meta");
  });

  it("Error", async () => {
    check(await body(await getCells(req("/api/v1/cells?bbox=bad"))), "Error", "400 body");
  });

  it("the response envelopes", async () => {
    check(await body(await getWards(req("/api/v1/wards?limit=1"))), "WardListResponse", "/wards");
    check(await body(await getCells(req("/api/v1/cells?limit=1"))), "CellListResponse", "/cells");
    check(
      await body(await getRecs(req("/api/v1/recommendations?limit=1"))),
      "RecommendationListResponse",
      "/recommendations"
    );
    check(
      await body(await getLookup(req("/api/v1/lookup?lat=19.076&lon=72.877"))),
      "LookupResponse",
      "/lookup"
    );
    check(
      await body(
        await getWard(req("/api/v1/wards/C"), { params: Promise.resolve({ wardId: "C" }) })
      ),
      "WardDetailResponse",
      "/wards/{wardId}"
    );
  });
});

describe("ward factor dominance (issue #97)", () => {
  it("reports which indicator drives each ward", async () => {
    const json = await body(await getWards(req("/api/v1/wards")));
    for (const ward of json.wards) {
      expect(ward).toHaveProperty("dominant_factor");
      expect(ward).toHaveProperty("dominant_share");
      expect(ward).toHaveProperty("single_factor_dominated");
    }
  });

  it("keeps the share a fraction and the flag consistent with it", async () => {
    const json = await body(await getWards(req("/api/v1/wards")));
    for (const ward of json.wards) {
      if (ward.dominant_share === null) continue;
      expect(ward.dominant_share).toBeGreaterThanOrEqual(0);
      expect(ward.dominant_share).toBeLessThanOrEqual(1);
      expect(ward.single_factor_dominated).toBe(ward.dominant_share >= 0.5);
    }
  });

  it("names a factor that is actually one of the contributions", async () => {
    const json = await body(await getWards(req("/api/v1/wards")));
    for (const ward of json.wards) {
      if (!ward.dominant_factor) continue;
      expect(Object.keys(ward.contrib ?? {})).toContain(ward.dominant_factor);
    }
  });
});

describe("GET /api/v1/export", () => {
  it("returns every cell as GeoJSON by default", async () => {
    const res = await getExport(req("/api/v1/export"));
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.type).toBe("FeatureCollection");
    expect(json.features).toHaveLength(541);
  });

  it("merges the NDVI change columns into the cell properties", async () => {
    const json = await (await getExport(req("/api/v1/export"))).json();
    const props = json.features[0].properties;
    expect(props).toHaveProperty("ndvi_delta");
    expect(props).toHaveProperty("change_class");
    // Present in cells_nbs, so the merge must not have replaced the base props.
    expect(props).toHaveProperty("HVI");
  });

  it("serves CSV with a header row and one row per cell", async () => {
    const res = await getExport(req("/api/v1/export?format=csv"));
    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("content-disposition")).toContain("ucip_cells.csv");

    const lines = (await res.text()).trim().split(/\r?\n/);
    expect(lines).toHaveLength(542);
    expect(lines[0].startsWith("grid_id,lon,lat,")).toBe(true);
  });

  it("puts a usable lon/lat on every CSV row, so no geometry library is needed", async () => {
    const text = await (await getExport(req("/api/v1/export?format=csv"))).text();
    const [header, ...rows] = text.trim().split(/\r?\n/);
    const columns = header.split(",");
    const lon = columns.indexOf("lon");
    const lat = columns.indexOf("lat");

    for (const row of rows) {
      const cells = row.split(",");
      // Mumbai's bbox, loosely. A centre outside it means the geometry
      // handling is wrong, which is the failure worth catching here.
      expect(Number(cells[lon])).toBeGreaterThan(72);
      expect(Number(cells[lon])).toBeLessThan(73.5);
      expect(Number(cells[lat])).toBeGreaterThan(18.5);
      expect(Number(cells[lat])).toBeLessThan(19.8);
    }
  });

  it("exports the 24 wards too", async () => {
    const json = await (await getExport(req("/api/v1/export?dataset=wards"))).json();
    expect(json.features).toHaveLength(24);
  });

  it("rejects an unknown dataset or format by name", async () => {
    const badDataset = await getExport(req("/api/v1/export?dataset=nope"));
    expect(badDataset.status).toBe(400);
    expect(JSON.stringify(await badDataset.json())).toContain("nope");

    const badFormat = await getExport(req("/api/v1/export?format=xlsx"));
    expect(badFormat.status).toBe(400);
    expect(JSON.stringify(await badFormat.json())).toContain("xlsx");
  });

  it("is edge-cached like the rest of the API", async () => {
    const res = await getExport(req("/api/v1/export?format=csv"));
    expect(res.headers.get("cache-control")).toContain("s-maxage=3600");
  });
});
