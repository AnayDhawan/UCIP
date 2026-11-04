import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { checkRateLimit } from "@/lib/rateLimit";
import { GET } from "./route";

// No Upstash store in tests, so the real limiter passes everything; the 429 case forces a refusal.
vi.mock("@/lib/rateLimit", () => ({ checkRateLimit: vi.fn(async () => null) }));

const ctx = (wardId: string) => ({ params: Promise.resolve({ wardId }) });
const req = new Request("https://uciplatform.vercel.app/api/weather/F-N");

const openMeteoBody = {
  current: { time: "2026-11-04T10:00", temperature_2m: 32.1, apparent_temperature: 37.4 },
  daily: {
    time: ["2026-11-04"],
    temperature_2m_max: [33],
    temperature_2m_min: [25],
    precipitation_probability_max: [10],
  },
};

beforeEach(() => {
  vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("GET /api/weather/{wardId}", () => {
  it("returns the forecast for a ward slug, asked of Open-Meteo at the ward's centroid", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () => ({ ok: true, json: async () => openMeteoBody }) as unknown as Response
    );
    vi.stubGlobal("fetch", fetchMock);

    const res = await GET(req, ctx("F-N"));

    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("public, s-maxage=1800, stale-while-revalidate=600");
    expect((await res.json()).temperatureC).toBe(32.1);
    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(Number(url.searchParams.get("latitude"))).toBeGreaterThan(18.8);
    expect(Number(url.searchParams.get("latitude"))).toBeLessThan(19.3);
    expect(url.searchParams.get("timezone")).toBe("Asia/Kolkata");
  });

  it("returns 404 for an unknown ward without calling Open-Meteo", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const res = await GET(req, ctx("ZZ"));

    expect(res.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns 502 with an error and no numbers when Open-Meteo fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 503 }) as unknown as Response));

    const res = await GET(req, ctx("F-N"));

    expect(res.status).toBe(502);
    expect(res.headers.get("cache-control")).toBe("public, s-maxage=30");
    expect(await res.json()).toEqual({ error: "Weather is unavailable right now." });
  });

  it("returns 429 without calling Open-Meteo when the client is over the limit", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    vi.mocked(checkRateLimit).mockResolvedValueOnce({
      ok: false,
      limit: 120,
      remaining: 0,
      retryAfterSeconds: 12,
    });

    const res = await GET(req, ctx("F-N"));

    expect(res.status).toBe(429);
    expect(res.headers.get("retry-after")).toBe("12");
    expect(res.headers.get("cache-control")).toBe("no-store");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
