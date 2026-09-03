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
import { GET as getCells } from "./cells/route";
import { GET as getSpec } from "./openapi.json/route";

const BASE = "https://uciplatform.vercel.app";

beforeAll(() => {
  // Force the snapshot path: no database configured. Both name pairs have to go,
  // since supabase() falls back from the unprefixed to the NEXT_PUBLIC_ names.
  delete process.env.SUPABASE_URL;
  delete process.env.SUPABASE_ANON_KEY;
  delete process.env.NEXT_PUBLIC_SUPABASE_URL;
  delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
});

const req = (path: string) => new Request(`${BASE}${path}`);
const body = async (res: Response) => JSON.parse(await res.text());

describe("GET /api/v1/meta", () => {
  it("reports coverage, counts and method", async () => {
    const res = await getMeta();
    expect(res.status).toBe(200);
    const json = await body(res);
    expect(json.counts.wards).toBe(24);
    expect(json.counts.citations).toBeGreaterThan(0);
    expect(json.license.code).toBe("Apache-2.0");
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
    ]) {
      expect(json.paths[path], `spec is missing ${path}`).toBeDefined();
    }
  });

  it("points its server URL at the requesting origin", async () => {
    const json = await body(await getSpec(req("/api/v1/openapi.json")));
    expect(json.servers[0].url).toBe(`${BASE}/api/v1`);
  });
});
