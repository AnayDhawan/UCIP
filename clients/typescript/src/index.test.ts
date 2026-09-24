/**
 * Client tests.
 *
 * These run against a stub fetch, not the network, so CI does not depend on a
 * deployment being up and the suite stays fast. What they pin is the part that
 * is actually easy to get wrong: URL construction, ward-code encoding, error
 * translation and parameter omission.
 *
 * There is one live test at the bottom, off unless UCIP_LIVE is set. A client
 * whose only tests use a stub it also wrote proves nothing about the real API,
 * and the release script runs it.
 */

import { describe, it, expect, vi } from "vitest";
import { UcipClient, UcipHttpError, UcipNetworkError, UcipError, DEFAULT_BASE_URL } from "./index.js";

/** A fetch that records its calls and replies with whatever is given. */
function stub(body: unknown, init: ResponseInit = {}) {
  const calls: string[] = [];
  const fetch = vi.fn(async (url: string | URL | Request) => {
    calls.push(String(url));
    const text = typeof body === "string" ? body : JSON.stringify(body);
    return new Response(text, { status: 200, ...init });
  }) as unknown as typeof globalThis.fetch;
  return { fetch, calls };
}

const client = (body: unknown, init?: ResponseInit) => {
  const s = stub(body, init);
  return { client: new UcipClient({ fetch: s.fetch }), calls: s.calls };
};

describe("URL construction", () => {
  it("defaults to the public deployment", () => {
    expect(new UcipClient().baseUrl).toBe(DEFAULT_BASE_URL);
  });

  it("strips a trailing slash so paths do not double up", () => {
    const c = new UcipClient({ baseUrl: "https://example.test/api/v1/" });
    expect(c.baseUrl).toBe("https://example.test/api/v1");
  });

  it("omits parameters that were not given", async () => {
    const { client: c, calls } = client({ wards: [] });
    await c.wards();
    expect(calls[0]).toBe(`${DEFAULT_BASE_URL}/wards`);
  });

  it("does not send the string 'undefined' for an explicit undefined", async () => {
    const { client: c, calls } = client({ wards: [] });
    await c.wards({ limit: undefined, geometry: true });
    expect(calls[0]).not.toContain("undefined");
    expect(calls[0]).toContain("geometry=true");
  });

  it("sends the parameters it was given", async () => {
    const { client: c, calls } = client({ cells: [] });
    await c.cells({ ward: "C", limit: 5, geometry: false });
    const url = new URL(calls[0]!);
    expect(url.searchParams.get("ward")).toBe("C");
    expect(url.searchParams.get("limit")).toBe("5");
    expect(url.searchParams.get("geometry")).toBe("false");
  });
});

describe("ward codes", () => {
  // The single most likely way to misuse this API by hand: F/N is a real ward
  // code and the slash breaks the path if it goes through unencoded.
  it("encodes the slash in a split ward code", async () => {
    const { client: c, calls } = client({ ward: {}, recommendations: [] });
    await c.ward("F/N");
    expect(calls[0]).toBe(`${DEFAULT_BASE_URL}/wards/F%2FN`);
  });

  it("leaves a simple code alone", async () => {
    const { client: c, calls } = client({ ward: {}, recommendations: [] });
    await c.ward("C");
    expect(calls[0]).toBe(`${DEFAULT_BASE_URL}/wards/C`);
  });

  it("trims incidental whitespace", async () => {
    const { client: c, calls } = client({ ward: {}, recommendations: [] });
    await c.ward("  L  ");
    expect(calls[0]).toBe(`${DEFAULT_BASE_URL}/wards/L`);
  });

  it("rejects an empty code at the call site rather than requesting /wards/", async () => {
    const { client: c, calls } = client({});
    await expect(c.ward("   ")).rejects.toThrow(TypeError);
    expect(calls).toHaveLength(0);
  });
});

describe("lookup", () => {
  it("sends the coordinate", async () => {
    const { client: c, calls } = client({ ward: {} });
    await c.lookup(19.076, 72.877);
    const url = new URL(calls[0]!);
    expect(url.searchParams.get("lat")).toBe("19.076");
    expect(url.searchParams.get("lon")).toBe("72.877");
  });

  it("refuses an out-of-range coordinate without a round trip", async () => {
    const { client: c, calls } = client({});
    await expect(c.lookup(91, 0)).rejects.toThrow(RangeError);
    await expect(c.lookup(0, 181)).rejects.toThrow(RangeError);
    await expect(c.lookup(Number.NaN, 0)).rejects.toThrow(RangeError);
    expect(calls).toHaveLength(0);
  });

  it("accepts the boundary values, which are real coordinates", async () => {
    const { client: c } = client({ ward: {} });
    await expect(c.lookup(-90, -180)).resolves.toBeDefined();
    await expect(c.lookup(90, 180)).resolves.toBeDefined();
  });
});

describe("errors", () => {
  it("throws UcipHttpError carrying the API's own message and hint", async () => {
    const { client: c } = client(
      { error: { status: 404, message: "No such ward.", hint: "Try /wards." } },
      { status: 404 }
    );
    const err = await c.ward("ZZ").catch((e) => e);
    expect(err).toBeInstanceOf(UcipHttpError);
    expect(err.status).toBe(404);
    expect(err.detail).toBe("No such ward.");
    expect(err.hint).toBe("Try /wards.");
    expect(err.isRateLimited).toBe(false);
  });

  it("surfaces retry-after on a 429 instead of retrying", async () => {
    const { client: c, calls } = client(
      { error: { status: 429, message: "Too many requests." } },
      { status: 429, headers: { "retry-after": "30" } }
    );
    const err = await c.wards().catch((e) => e);
    expect(err.isRateLimited).toBe(true);
    expect(err.retryAfterSeconds).toBe(30);
    // One attempt. A retry against a rate limiter makes the situation worse.
    expect(calls).toHaveLength(1);
  });

  it("survives an error body that is not the API's envelope", async () => {
    // An edge proxy returns HTML, and failing to parse it must not replace a
    // useful 502 with a JSON syntax error.
    const { client: c } = client("<html>502 Bad Gateway</html>", { status: 502 });
    const err = await c.meta().catch((e) => e);
    expect(err).toBeInstanceOf(UcipHttpError);
    expect(err.status).toBe(502);
    expect(err.detail).toBeUndefined();
    expect(err.body).toContain("502");
  });

  it("wraps a transport failure as UcipNetworkError", async () => {
    const fetch = vi.fn(async () => {
      throw new TypeError("fetch failed");
    }) as unknown as typeof globalThis.fetch;
    const err = await new UcipClient({ fetch }).meta().catch((e) => e);
    expect(err).toBeInstanceOf(UcipNetworkError);
    expect(err.cause).toBeInstanceOf(TypeError);
  });

  it("every error is catchable as UcipError", async () => {
    const { client: c } = client({ error: { status: 400, message: "bad" } }, { status: 400 });
    const err = await c.wards().catch((e) => e);
    expect(err).toBeInstanceOf(UcipError);
    expect(err.name).toBe("UcipHttpError");
  });

  it("rethrows a caller's abort untouched", async () => {
    const controller = new AbortController();
    const fetch = vi.fn(async () => {
      controller.abort();
      const e = new Error("aborted");
      e.name = "AbortError";
      throw e;
    }) as unknown as typeof globalThis.fetch;
    const err = await new UcipClient({ fetch }).meta(controller.signal).catch((e) => e);
    expect(err.name).toBe("AbortError");
    expect(err).not.toBeInstanceOf(UcipNetworkError);
  });
});

describe("convenience methods", () => {
  it("allWards unwraps the envelope", async () => {
    const { client: c } = client({ source: "database", count: 1, wards: [{ ward_id: "C" }] });
    expect(await c.allWards()).toEqual([{ ward_id: "C" }]);
  });

  it("export asks for geojson", async () => {
    const { client: c, calls } = client({ type: "FeatureCollection", features: [] });
    await c.export("wards");
    const url = new URL(calls[0]!);
    expect(url.searchParams.get("dataset")).toBe("wards");
    expect(url.searchParams.get("format")).toBe("geojson");
  });

  it("exportCsv asks for csv and returns text", async () => {
    const { client: c, calls } = client("ward_id,lon,lat\nC,72.8,19.0\n");
    const csv = await c.exportCsv("wards");
    expect(new URL(calls[0]!).searchParams.get("format")).toBe("csv");
    expect(csv.split("\n")[0]).toBe("ward_id,lon,lat");
  });
});

describe("options", () => {
  it("passes custom headers", async () => {
    const seen: Array<Record<string, string>> = [];
    const fetch = vi.fn(async (_url: unknown, init: RequestInit) => {
      seen.push(init.headers as Record<string, string>);
      return new Response("{}", { status: 200 });
    }) as unknown as typeof globalThis.fetch;
    await new UcipClient({ fetch, headers: { "user-agent": "my-tool/1.0" } }).meta();
    expect(seen[0]!["user-agent"]).toBe("my-tool/1.0");
  });

  it("falls back to the global fetch when none is given", () => {
    // `??` treats both undefined and null as "not supplied", so either one
    // means the global fetch, which Node 18 and every browser have.
    expect(() => new UcipClient()).not.toThrow();
    expect(() => new UcipClient({ fetch: undefined })).not.toThrow();
  });

  it("refuses a supplied fetch that is not callable", () => {
    // The guard is for the case where something was passed and it is wrong,
    // which otherwise fails later with a confusing 'not a function'.
    expect(() => new UcipClient({ fetch: 42 as never })).toThrow(/No fetch available/);
  });
});

/**
 * The live check. Off unless UCIP_LIVE is set, because CI should not fail when
 * somebody else's deployment is down, but a client only tested against its own
 * stub has proven nothing about the API it claims to speak to.
 */
describe.runIf(process.env.UCIP_LIVE)("against the live API", () => {
  const live = new UcipClient({ timeoutMs: 30_000 });

  it("returns 24 wards, ranked", async () => {
    const wards = await live.allWards();
    expect(wards).toHaveLength(24);
    expect(wards[0]!.rank).toBe(1);
    expect(typeof wards[0]!.hvi).toBe("number");
  });

  it("resolves a split ward code over the wire", async () => {
    const { ward } = await live.ward("F/N");
    expect(ward.ward_id).toBe("F/N");
  });

  it("looks up a coordinate", async () => {
    const { ward } = await live.lookup(19.076, 72.877);
    expect(ward.ward_id).toBe("L");
  });

  it("404s a point outside every ward", async () => {
    const err = await live.lookup(0, 0).catch((e) => e);
    expect(err).toBeInstanceOf(UcipHttpError);
    expect(err.status).toBe(404);
  });

  it("exports the whole dataset in one call", async () => {
    const fc = await live.export("wards");
    expect(fc.type).toBe("FeatureCollection");
    expect(fc.features).toHaveLength(24);
  });
});
