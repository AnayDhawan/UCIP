/**
 * Issue #43.
 *
 * useWardData backs both the sidebar detail view and the fullscreen/mobile ward
 * dialog, so a regression here breaks the ward surfaces on every screen size at
 * once. Two behaviours matter most and are easy to lose in a refactor:
 *
 *   1. wards are sorted by rank, most vulnerable first, because the ward list
 *      renders in array order and would otherwise show an arbitrary ordering.
 *   2. the ward_profiles.json fetch is additive. Its failure must leave wards
 *      and recs intact, since a ward without its descriptive profile still has a
 *      score, a breakdown and interventions worth showing.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useWardData } from "./useWardData";

const wardsFixture = {
  type: "FeatureCollection",
  features: [
    { type: "Feature", geometry: null, properties: { ward_id: "L", HVI: 61, rank: 3 } },
    { type: "Feature", geometry: null, properties: { ward_id: "F/N", HVI: 78, rank: 1 } },
    { type: "Feature", geometry: null, properties: { ward_id: "G/N", HVI: 70, rank: 2 } },
  ],
};

const recsFixture = [
  { ward_id: "F/N", intervention: "Native tree planting", priority: 1 },
  { ward_id: "G/N", intervention: "Cool roofs", priority: 2 },
];

const profilesFixture = { n_wards: 3, wards: [{ ward_id: "F/N" }] };

const json = (body: unknown) => ({ ok: true, json: async () => body }) as unknown as Response;

/** The same three wards as the API returns them: lowercase keys, nested contrib. */
const apiWardsFixture = {
  source: "database",
  count: 3,
  wards: [
    { ward_id: "L", hvi: 61, rank: 3, n_cells: 5, contrib: { LST_C: 0.2 }, geom_geojson: { type: "Polygon", coordinates: [] } },
    { ward_id: "F/N", hvi: 78, rank: 1, n_cells: 9, contrib: { LST_C: 0.4 }, geom_geojson: { type: "Polygon", coordinates: [] } },
    { ward_id: "G/N", hvi: 70, rank: 2, n_cells: 7, contrib: { LST_C: 0.3 }, geom_geojson: { type: "Polygon", coordinates: [] } },
  ],
};

const apiRecsFixture = { source: "database", count: 2, recommendations: recsFixture };

/**
 * Routes each of the hook's fetches to a caller-supplied handler.
 *
 * The hook now tries /api/v1 first and falls back to the static snapshot, so
 * both routes are stubbed separately and a test can fail one to exercise the
 * other.
 */
function stubFetch(handlers: {
  apiWards?: () => Promise<Response>;
  apiRecs?: () => Promise<Response>;
  wards?: () => Promise<Response>;
  recs?: () => Promise<Response>;
  profiles?: () => Promise<Response>;
}) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (url.includes("/api/v1/wards"))
        return (handlers.apiWards ?? (async () => json(apiWardsFixture)))();
      if (url.includes("/api/v1/recommendations"))
        return (handlers.apiRecs ?? (async () => json(apiRecsFixture)))();
      if (url.includes("wards_hvi")) return (handlers.wards ?? (async () => json(wardsFixture)))();
      if (url.includes("nbs_recommendations"))
        return (handlers.recs ?? (async () => json(recsFixture)))();
      if (url.includes("ward_profiles"))
        return (handlers.profiles ?? (async () => json(profilesFixture)))();
      throw new Error(`unexpected fetch: ${url}`);
    })
  );
}

/** Makes the API unavailable so the hook has to use the static snapshots. */
const apiDown = {
  apiWards: async () => ({ ok: false, status: 503 }) as unknown as Response,
  apiRecs: async () => ({ ok: false, status: 503 }) as unknown as Response,
};

beforeEach(() => {
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("useWardData loading state", () => {
  it("starts with everything null and no error", () => {
    stubFetch({});
    const { result } = renderHook(() => useWardData());

    expect(result.current.wards).toBeNull();
    expect(result.current.recs).toBeNull();
    expect(result.current.profiles).toBeNull();
    expect(result.current.error).toBeNull();
  });
});

describe("useWardData success state", () => {
  it("resolves wards, recs and profiles", async () => {
    stubFetch({});
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.wards).not.toBeNull());
    await waitFor(() => expect(result.current.profiles).not.toBeNull());

    expect(result.current.wards).toHaveLength(3);
    expect(result.current.recs).toEqual(recsFixture);
    expect(result.current.profiles).toEqual(profilesFixture);
    expect(result.current.error).toBeNull();
  });

  it("sorts wards by rank, most vulnerable first", async () => {
    stubFetch({});
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.wards).not.toBeNull());
    expect(result.current.wards!.map((w) => w.properties.ward_id)).toEqual(["F/N", "G/N", "L"]);
  });

  it("sorts wards with a missing rank to the end instead of dropping them", async () => {
    stubFetch({
      ...apiDown,
      wards: async () =>
        json({
          type: "FeatureCollection",
          features: [
            { type: "Feature", geometry: null, properties: { ward_id: "X", HVI: 5 } },
            { type: "Feature", geometry: null, properties: { ward_id: "F/N", HVI: 78, rank: 1 } },
          ],
        }),
    });
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.wards).not.toBeNull());
    expect(result.current.wards!.map((w) => w.properties.ward_id)).toEqual(["F/N", "X"]);
  });
});

describe("useWardData error state", () => {
  it("sets error and does not hang in loading when the wards fetch fails", async () => {
    // The hook only surfaces an error when BOTH the API and its snapshot
    // fallback fail; either one alone is designed to be survivable.
    stubFetch({
      apiWards: async () => {
        throw new Error("api down");
      },
      wards: async () => {
        throw new Error("network down");
      },
    });
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain("network down");
    expect(result.current.wards).toBeNull();
    expect(result.current.recs).toBeNull();
  });

  it("sets error when the recommendations fetch fails", async () => {
    stubFetch({
      apiRecs: async () => {
        throw new Error("api down");
      },
      recs: async () => {
        throw new Error("recs unavailable");
      },
    });
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain("recs unavailable");
  });
});

describe("useWardData treats the profile fetch as additive", () => {
  it("still returns wards and recs when the profile fetch rejects", async () => {
    stubFetch({
      profiles: async () => {
        throw new Error("profiles missing");
      },
    });
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.wards).not.toBeNull());

    expect(result.current.wards).toHaveLength(3);
    expect(result.current.recs).toEqual(recsFixture);
    expect(result.current.profiles).toBeNull();
    // The documented contract: a missing profile is not an error state, because
    // the ward still has a score, a breakdown and interventions to show.
    expect(result.current.error).toBeNull();
  });

  it("still returns wards and recs on a 404 for the profile file", async () => {
    stubFetch({
      profiles: async () => ({ ok: false, status: 404 }) as unknown as Response,
    });
    const { result } = renderHook(() => useWardData());

    await waitFor(() => expect(result.current.wards).not.toBeNull());
    expect(result.current.profiles).toBeNull();
    expect(result.current.error).toBeNull();
  });
});

describe("useWardData reads live data first (#53)", () => {
  it("prefers the API over the static snapshots", async () => {
    stubFetch({});
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.wards).not.toBeNull());

    const calls = (globalThis.fetch as unknown as { mock: { calls: [string][] } }).mock.calls.map(
      (c) => c[0]
    );
    expect(calls.some((u) => u.includes("/api/v1/wards"))).toBe(true);
    // The snapshot must not be fetched at all when the API answered.
    expect(calls.some((u) => u.includes("wards_hvi"))).toBe(false);
  });

  it("reshapes the API's lowercase keys into the shape components expect", async () => {
    stubFetch({});
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.wards).not.toBeNull());

    const top = result.current.wards![0].properties;
    expect(top.ward_id).toBe("F/N");
    // API sends `hvi`; components read `HVI`.
    expect(top.HVI).toBe(78);
    expect(top.rank).toBe(1);
    // API nests contributions; components read flat contrib_* fields.
    expect(top.contrib_LST_C).toBe(0.4);
  });

  it("still sorts by rank when the data comes from the API", async () => {
    stubFetch({});
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.wards).not.toBeNull());
    expect(result.current.wards!.map((w) => w.properties.ward_id)).toEqual(["F/N", "G/N", "L"]);
  });

  it("falls back to the static snapshots when the API is down", async () => {
    // The property that matters most: the Supabase project was deleted once
    // already, and the dashboard has to survive that.
    stubFetch(apiDown);
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.wards).not.toBeNull());

    expect(result.current.wards).toHaveLength(3);
    expect(result.current.recs).toEqual(recsFixture);
    expect(result.current.error).toBeNull();
  });

  it("falls back when the API answers but carries no geometry", async () => {
    // A ward with no polygon cannot be drawn, so an otherwise-successful
    // response missing geometry is worse than useless: it would render an empty
    // map with no error.
    stubFetch({
      apiWards: async () =>
        json({ wards: [{ ward_id: "L", hvi: 61, rank: 1, n_cells: 5, contrib: {} }] }),
    });
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.wards).not.toBeNull());

    // Fell through to the snapshot's three wards rather than accepting the
    // single geometry-less ward the API returned.
    expect(result.current.wards).toHaveLength(3);
    expect(result.current.wards!.map((w) => w.properties.ward_id)).toEqual(["F/N", "G/N", "L"]);
  });

  it("falls back for recommendations independently of wards", async () => {
    stubFetch({ apiRecs: async () => ({ ok: false, status: 500 }) as unknown as Response });
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.recs).not.toBeNull());
    expect(result.current.recs).toEqual(recsFixture);
    expect(result.current.error).toBeNull();
  });
});

describe("useWardData fetching discipline", () => {
  it("fetches each file exactly once per mount", async () => {
    // A duplicate nbs_recommendations fetch was removed once already (the
    // 2026-07-30 ward-dialog work); this keeps it from creeping back.
    stubFetch({});
    const { result } = renderHook(() => useWardData());
    await waitFor(() => expect(result.current.profiles).not.toBeNull());

    const calls = (globalThis.fetch as unknown as { mock: { calls: [string][] } }).mock.calls.map(
      (c) => c[0]
    );
    expect(calls.filter((u) => u.includes("/api/v1/wards"))).toHaveLength(1);
    expect(calls.filter((u) => u.includes("/api/v1/recommendations"))).toHaveLength(1);
    expect(calls.filter((u) => u.includes("ward_profiles"))).toHaveLength(1);
  });

  it("does not set state after unmount", async () => {
    let resolveWards: (r: Response) => void = () => {};
    stubFetch({
      apiWards: () => new Promise<Response>((res) => (resolveWards = res)),
    });

    const { unmount } = renderHook(() => useWardData());
    unmount();
    resolveWards(json(apiWardsFixture));

    // The hook guards every setState with a `cancelled` flag. If that guard were
    // removed, React would warn here about updating an unmounted component.
    await new Promise((r) => setTimeout(r, 20));
    expect(console.error).not.toHaveBeenCalled();
  });
});
