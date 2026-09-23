/**
 * Tests for the UCIP MCP server (issue #102).
 *
 * The acceptance criterion is that a client gets the same data as the
 * equivalent REST call, so the tools are exercised against a stubbed API whose
 * responses are the real shapes, and the assertions check that what comes back
 * is the endpoint's own data rather than a reshaped version of it.
 *
 * The other property worth pinning is the one an assistant can quietly undo:
 * every response has to carry its caveats. A ranking handed to a language
 * model without them comes back out as a confident recommendation with the
 * uncertainty sanded off.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

const wards = [
  { ward_id: "C", hvi: 73.56, rank: 1, n_cells: 2, contrib: { LST_C: 0.22 }, dominant_factor: "LST_C" },
  { ward_id: "G/N", hvi: 69.67, rank: 2, n_cells: 9, contrib: { NDVI: 0.19 }, dominant_factor: "NDVI" },
];

const recommendations = [
  {
    ward_id: "C",
    intervention: "Cool roofs + reflective pavements + cooling centres",
    rationale: "High vulnerability, low canopy, but native-grassland/built-up cell",
    citation: "Veldman et al. 2019, Science (response to Bastin 2019)",
    priority: 1,
  },
];

let lastUrl = "";
const routes: Record<string, unknown> = {};

const stubFetch = vi.fn(async (input: RequestInfo | URL) => {
  lastUrl = String(input);
  const path = new URL(lastUrl).pathname.replace("/api/v1", "");
  const body = routes[path];
  if (body === undefined) {
    return new Response(JSON.stringify({ error: { message: "Not found" } }), {
      status: 404,
      headers: { "content-type": "application/json" },
    });
  }
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}) as unknown as typeof globalThis.fetch;

vi.stubGlobal("fetch", stubFetch);

const { callTool, TOOLS, RANKING_CAVEAT } = await import("./index.js");

beforeEach(() => {
  lastUrl = "";
  for (const key of Object.keys(routes)) delete routes[key];
  routes["/meta"] = { name: "UCIP", counts: { wards: 24 }, method: { index: "HVI" } };
  routes["/wards"] = { source: "database", count: 2, wards };
  routes["/wards/C"] = { source: "database", ward: wards[0], recommendations };
  routes["/wards/F%2FN"] = { source: "database", ward: { ward_id: "F/N", rank: 5 }, recommendations: [] };
  routes["/lookup"] = { source: "database", ward: wards[0], top_recommendation: recommendations[0] };
  routes["/recommendations"] = { source: "database", count: 1, recommendations };
});

const parse = async (name: string, args: Record<string, unknown> = {}) =>
  JSON.parse(await callTool(name, args));

describe("tool catalogue", () => {
  it("exposes exactly the five tools the issue asked for", () => {
    expect(TOOLS.map((t) => t.name).sort()).toEqual([
      "get_methodology",
      "get_recommendations",
      "get_ward",
      "list_wards",
      "lookup_ward",
    ]);
  });

  it("gives every tool a description an assistant can route on", () => {
    for (const tool of TOOLS) {
      expect(tool.description.length).toBeGreaterThan(40);
      expect(tool.inputSchema.type).toBe("object");
    }
  });

  it("marks the arguments that are genuinely required", () => {
    const byName = Object.fromEntries(TOOLS.map((t) => [t.name, t]));
    expect((byName.get_ward!.inputSchema as { required?: string[] }).required).toEqual(["ward_id"]);
    expect((byName.lookup_ward!.inputSchema as { required?: string[] }).required).toEqual(["lat", "lon"]);
  });
});

describe("list_wards", () => {
  it("returns the endpoint's own ward rows", async () => {
    const result = await parse("list_wards");
    expect(result.wards).toEqual(wards);
  });

  it("passes limit through to the API", async () => {
    await callTool("list_wards", { limit: 5 });
    expect(lastUrl).toContain("limit=5");
  });

  it("carries the ranking caveat, which is the whole point", async () => {
    const result = await parse("list_wards");
    expect(result._notes.join(" ")).toContain("no ward's rank is certain");
  });
});

describe("get_ward", () => {
  it("returns the ward and its recommendations unchanged", async () => {
    const result = await parse("get_ward", { ward_id: "C" });
    expect(result.ward).toEqual(wards[0]);
    expect(result.recommendations).toEqual(recommendations);
  });

  it("uppercases a lowercase code rather than 404ing", async () => {
    const result = await parse("get_ward", { ward_id: "c" });
    expect(result.ward.ward_id).toBe("C");
  });

  it("url-encodes a split ward code, which contains a slash", async () => {
    // F/N unencoded would split the path into two segments and 404.
    const result = await parse("get_ward", { ward_id: "F/N" });
    expect(lastUrl).toContain("F%2FN");
    expect(result.ward.ward_id).toBe("F/N");
  });

  it("refuses an empty ward id before calling the API", async () => {
    await expect(callTool("get_ward", { ward_id: "" })).rejects.toThrow("ward_id is required");
  });

  it("tells the assistant to quote the citation with the recommendation", async () => {
    const result = await parse("get_ward", { ward_id: "C" });
    expect(result._notes.join(" ")).toContain("Quote it with the recommendation");
  });
});

describe("lookup_ward", () => {
  it("resolves a coordinate to a ward", async () => {
    const result = await parse("lookup_ward", { lat: 19.076, lon: 72.877 });
    expect(result.ward.ward_id).toBe("C");
    expect(lastUrl).toContain("lat=19.076");
    expect(lastUrl).toContain("lon=72.877");
  });

  it("refuses non-numeric coordinates before calling the API", async () => {
    await expect(callTool("lookup_ward", { lat: "north", lon: 72 })).rejects.toThrow(
      "must be numbers"
    );
  });

  it("says coverage is Mumbai only, so a miss is not read as no risk", async () => {
    const result = await parse("lookup_ward", { lat: 19.076, lon: 72.877 });
    expect(result._notes.join(" ")).toContain("Mumbai only");
  });
});

describe("get_recommendations", () => {
  it("returns recommendations for one ward", async () => {
    const result = await parse("get_recommendations", { ward_id: "C" });
    expect(result.recommendations).toEqual(recommendations);
    expect(lastUrl).toContain("ward=C");
  });

  it("works with no ward at all", async () => {
    const result = await parse("get_recommendations");
    expect(result.recommendations).toHaveLength(1);
    expect(lastUrl).not.toContain("ward=");
  });

  it("explains why trees are absent where they are absent", async () => {
    // Without this an assistant reads a missing intervention as an oversight
    // and helpfully suggests planting the thing the filter refused.
    const result = await parse("get_recommendations");
    expect(result._notes.join(" ")).toContain("Veldman");
  });
});

describe("get_methodology", () => {
  it("returns meta with its proxy caveats attached", async () => {
    const result = await parse("get_methodology");
    expect(result.counts.wards).toBe(24);
    const notes = result._notes.join(" ");
    expect(notes).toContain("proxies");
    expect(notes).toContain("not air temperature");
  });
});

describe("failure handling", () => {
  it("surfaces an API error with its status rather than a bare throw", async () => {
    delete routes["/wards/ZZ"];
    await expect(callTool("get_ward", { ward_id: "ZZ" })).rejects.toThrow("Not found");
  });

  it("rejects an unknown tool by name", async () => {
    await expect(callTool("drop_database", {})).rejects.toThrow("Unknown tool");
  });
});

describe("caveats", () => {
  it("attaches notes to every tool that returns scores or ranks", async () => {
    for (const name of ["list_wards", "get_ward", "lookup_ward", "get_recommendations", "get_methodology"]) {
      const args = name === "get_ward" ? { ward_id: "C" } : name === "lookup_ward" ? { lat: 19, lon: 72 } : {};
      const result = await parse(name, args);
      expect(Array.isArray(result._notes), `${name} should carry notes`).toBe(true);
      expect(result._notes.length, `${name} should carry at least one note`).toBeGreaterThan(0);
    }
  });

  it("states the uncertainty as a number, not as a vague hedge", () => {
    expect(RANKING_CAVEAT).toMatch(/6 places/);
  });
});
