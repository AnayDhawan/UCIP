/**
 * Issue #41.
 *
 * fetchCityTemp has one invariant that matters more than everything else in the
 * file: on any failure it returns null, never a number. The widget's whole
 * justification is showing a real live reading next to the map's satellite
 * proxy, and UCIP's product rule is that numbers are real or absent. A
 * well-meaning "fall back to 30C so the widget isn't empty" would quietly turn
 * the one live figure on the page into a fabrication, so these tests are written
 * to fail loudly if anyone ever adds one.
 *
 * (The issue refers to this as fetchMumbaiTemp; it was renamed to fetchCityTemp
 * by issue #17 when the hardcoded Mumbai coordinates were moved into city.ts.)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchCityTemp, fetchPointForecast } from "./weather";
import { MUMBAI } from "./city";

const okResponse = (body: unknown) =>
  ({ ok: true, json: async () => body }) as unknown as Response;

beforeEach(() => {
  // The failure paths log to console.error by design; keep the test output clean.
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("fetchCityTemp success path", () => {
  it("parses the temperature and observation time", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => okResponse({ current: { temperature_2m: 31.4, time: "2026-09-03T09:00" } }))
    );

    const result = await fetchCityTemp(MUMBAI);
    expect(result).toEqual({ temperatureC: 31.4, observedAt: "2026-09-03T09:00" });
  });

  it("accepts a reading of exactly zero", async () => {
    // 0 is falsy. A truthiness check instead of a typeof check would discard a
    // legitimate reading here.
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => okResponse({ current: { temperature_2m: 0, time: "2026-01-01T06:00" } }))
    );

    const result = await fetchCityTemp(MUMBAI);
    expect(result).not.toBeNull();
    expect(result!.temperatureC).toBe(0);
  });

  it("tolerates a missing timestamp without discarding the reading", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => okResponse({ current: { temperature_2m: 29 } })));

    const result = await fetchCityTemp(MUMBAI);
    expect(result).toEqual({ temperatureC: 29, observedAt: "" });
  });

  it("queries the coordinates of the city it is given, not a hardcoded location", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () =>
      okResponse({ current: { temperature_2m: 20, time: "2026-09-03T09:00" } })
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchCityTemp({
      slug: "pune",
      name: "Pune",
      center: [18.5204, 73.8567],
      zoom: 11,
      bbox: [73.7, 18.4, 74.0, 18.65],
      lat: 18.5204,
      lon: 73.8567,
      timezone: "Asia/Kolkata",
    });

    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(url.searchParams.get("latitude")).toBe("18.5204");
    expect(url.searchParams.get("longitude")).toBe("73.8567");
    expect(url.searchParams.get("current")).toBe("temperature_2m");
  });
});

describe("fetchCityTemp failure paths all return null", () => {
  it("returns null on a network error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
    expect(await fetchCityTemp(MUMBAI)).toBeNull();
  });

  it("returns null on an abort/timeout", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        const err = new Error("The operation was aborted.");
        err.name = "AbortError";
        throw err;
      })
    );
    expect(await fetchCityTemp(MUMBAI)).toBeNull();
  });

  it("returns null on a non-OK HTTP status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 503, json: async () => ({}) }) as unknown as Response)
    );
    expect(await fetchCityTemp(MUMBAI)).toBeNull();
  });

  it("returns null on a malformed body", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => okResponse({})));
    expect(await fetchCityTemp(MUMBAI)).toBeNull();

    vi.stubGlobal("fetch", vi.fn(async () => okResponse({ current: {} })));
    expect(await fetchCityTemp(MUMBAI)).toBeNull();

    vi.stubGlobal("fetch", vi.fn(async () => okResponse({ current: { temperature_2m: null } })));
    expect(await fetchCityTemp(MUMBAI)).toBeNull();
  });

  it("returns null when the temperature is a string rather than a number", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => okResponse({ current: { temperature_2m: "31.4", time: "x" } }))
    );
    expect(await fetchCityTemp(MUMBAI)).toBeNull();
  });

  it("returns null when the response body is not JSON at all", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          ({
            ok: true,
            json: async () => {
              throw new SyntaxError("Unexpected token < in JSON");
            },
          }) as unknown as Response
      )
    );
    expect(await fetchCityTemp(MUMBAI)).toBeNull();
  });

  it("never returns a fabricated fallback number on any failure", async () => {
    // The regression this whole suite exists to prevent. If someone adds a
    // default temperature on the error path, every case below starts returning
    // an object and this fails.
    const failures = [
      async () => {
        throw new Error("network");
      },
      async () => ({ ok: false, status: 500, json: async () => ({}) }) as unknown as Response,
      async () => okResponse({}),
      async () => okResponse({ current: { temperature_2m: undefined } }),
    ];

    for (const impl of failures) {
      vi.stubGlobal("fetch", vi.fn(impl));
      expect(await fetchCityTemp(MUMBAI)).toBeNull();
    }
  });
});

describe("fetchCityTemp request shape", () => {
  it("passes an abort signal so the request cannot hang forever", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () =>
      okResponse({ current: { temperature_2m: 30, time: "2026-09-03T09:00" } })
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchCityTemp(MUMBAI);

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });
});

const FORECAST_BODY = {
  current: { time: "2026-11-04T10:00", temperature_2m: 32.1, apparent_temperature: 37.4 },
  daily: {
    time: ["2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10"],
    temperature_2m_max: [33, 34, 33.5, 32, 31, 32, 33],
    temperature_2m_min: [25, 25.5, 26, 24, 24, 25, 25],
    precipitation_probability_max: [0, 5, null, 20, 40, 10, 0],
  },
};

describe("fetchPointForecast", () => {
  it("parses current conditions and seven daily rows", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => okResponse(FORECAST_BODY)));

    const result = await fetchPointForecast(19.07, 72.88, "Asia/Kolkata");
    expect(result).toMatchObject({
      temperatureC: 32.1,
      apparentC: 37.4,
      observedAt: "2026-11-04T10:00",
    });
    expect(result!.days).toHaveLength(7);
    expect(result!.days[0]).toEqual({ date: "2026-11-04", maxC: 33, minC: 25, rainChancePct: 0 });
  });

  it("keeps a missing rain probability as null instead of inventing a number", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => okResponse(FORECAST_BODY)));

    const result = await fetchPointForecast(19.07, 72.88, "Asia/Kolkata");
    expect(result!.days[2].rainChancePct).toBeNull();
  });

  it("asks for the point, the fields, seven days and the city timezone", async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => okResponse(FORECAST_BODY));
    vi.stubGlobal("fetch", fetchMock);

    await fetchPointForecast(19.07, 72.88, "Asia/Kolkata");

    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(url.origin + url.pathname).toBe("https://api.open-meteo.com/v1/forecast");
    expect(url.searchParams.get("latitude")).toBe("19.07");
    expect(url.searchParams.get("longitude")).toBe("72.88");
    expect(url.searchParams.get("current")).toBe("temperature_2m,apparent_temperature");
    expect(url.searchParams.get("daily")).toBe(
      "temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    );
    expect(url.searchParams.get("forecast_days")).toBe("7");
    expect(url.searchParams.get("timezone")).toBe("Asia/Kolkata");
    expect((fetchMock.mock.calls[0][1] as RequestInit).signal).toBeInstanceOf(AbortSignal);
  });

  it("returns null on a network error, a non-OK status, or a body that is not JSON", async () => {
    const failures = [
      async () => {
        throw new TypeError("Failed to fetch");
      },
      async () => ({ ok: false, status: 503, json: async () => ({}) }) as unknown as Response,
      async () =>
        ({
          ok: true,
          json: async () => {
            throw new SyntaxError("Unexpected token < in JSON");
          },
        }) as unknown as Response,
    ];

    for (const impl of failures) {
      vi.stubGlobal("fetch", vi.fn(impl));
      expect(await fetchPointForecast(19.07, 72.88, "Asia/Kolkata")).toBeNull();
    }
  });

  it("returns null on a malformed body rather than partial or fabricated numbers", async () => {
    const bodies = [
      {},
      { ...FORECAST_BODY, current: { time: "x", temperature_2m: 30 } },
      { ...FORECAST_BODY, current: { time: "x", temperature_2m: "30", apparent_temperature: 35 } },
      { current: FORECAST_BODY.current },
      { ...FORECAST_BODY, daily: { ...FORECAST_BODY.daily, temperature_2m_max: [33, null] } },
      { ...FORECAST_BODY, daily: { ...FORECAST_BODY.daily, time: [] } },
    ];

    for (const body of bodies) {
      vi.stubGlobal("fetch", vi.fn(async () => okResponse(body)));
      expect(await fetchPointForecast(19.07, 72.88, "Asia/Kolkata")).toBeNull();
    }
  });
});
