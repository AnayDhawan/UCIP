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

/** Routes each of the hook's three fetches to a caller-supplied handler. */
function stubFetch(handlers: {
  wards?: () => Promise<Response>;
  recs?: () => Promise<Response>;
  profiles?: () => Promise<Response>;
}) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      if (url.includes("wards_hvi")) return (handlers.wards ?? (async () => json(wardsFixture)))();
      if (url.includes("nbs_recommendations"))
        return (handlers.recs ?? (async () => json(recsFixture)))();
      if (url.includes("ward_profiles"))
        return (handlers.profiles ?? (async () => json(profilesFixture)))();
      throw new Error(`unexpected fetch: ${url}`);
    })
  );
}

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
    stubFetch({
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
    expect(calls.filter((u) => u.includes("wards_hvi"))).toHaveLength(1);
    expect(calls.filter((u) => u.includes("nbs_recommendations"))).toHaveLength(1);
    expect(calls.filter((u) => u.includes("ward_profiles"))).toHaveLength(1);
  });

  it("does not set state after unmount", async () => {
    let resolveWards: (r: Response) => void = () => {};
    stubFetch({
      wards: () => new Promise<Response>((res) => (resolveWards = res)),
    });

    const { unmount } = renderHook(() => useWardData());
    unmount();
    resolveWards(json(wardsFixture));

    // The hook guards every setState with a `cancelled` flag. If that guard were
    // removed, React would warn here about updating an unmounted component.
    await new Promise((r) => setTimeout(r, 20));
    expect(console.error).not.toHaveBeenCalled();
  });
});
