import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import WardWeather, { WEATHER_LABEL } from "./WardWeather";

const forecast = {
  temperatureC: 32.1,
  apparentC: 37.4,
  observedAt: "2026-11-04T10:00",
  days: [
    { date: "2026-11-04", maxC: 33.2, minC: 25.4, rainChancePct: 0 },
    { date: "2026-11-05", maxC: 34.6, minC: 25.5, rainChancePct: null },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("WardWeather", () => {
  it("shows current and feels-like temperature, the daily row and the Open-Meteo label", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => forecast }) as unknown as Response);
    vi.stubGlobal("fetch", fetchMock);

    render(<WardWeather wardId="F/N" />);

    expect(await screen.findByText("32.1°C")).toBeInTheDocument();
    expect(screen.getByText("37.4°C")).toBeInTheDocument();
    expect(screen.getByLabelText("Wed: high 33, low 25 degrees")).toBeInTheDocument();
    expect(screen.getByLabelText("Thu: high 35, low 26 degrees")).toBeInTheDocument();
    expect(WEATHER_LABEL).toBe("Forecast by Open-Meteo. UCIP's heat score is not a forecast.");
    expect(screen.getByText(WEATHER_LABEL)).toBeInTheDocument();
    // The route takes the slug, not the raw code with its slash.
    expect(fetchMock).toHaveBeenCalledWith("/api/weather/F-N");
  });

  it("says weather is unavailable, with no numbers, when the route fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 502 }) as unknown as Response));

    render(<WardWeather wardId="A" />);

    expect(await screen.findByText("Weather unavailable right now.")).toBeInTheDocument();
    expect(screen.queryByText(/°/)).toBeNull();
    expect(screen.getByText(WEATHER_LABEL)).toBeInTheDocument();
  });

  it("says weather is unavailable when the request itself throws", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    }));

    render(<WardWeather wardId="A" />);

    expect(await screen.findByText("Weather unavailable right now.")).toBeInTheDocument();
  });

  it("shows a loading line before the request settles", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));

    render(<WardWeather wardId="A" />);

    expect(screen.getByText("Loading weather.")).toBeInTheDocument();
  });
});
