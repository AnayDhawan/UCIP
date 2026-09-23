import { describe, expect, it } from "vitest";
import { parseMapLayer, parseMapView, writeMapView } from "./mapState";

describe("dashboard map URL state", () => {
  it("accepts a complete valid view", () => {
    expect(parseMapView(new URLSearchParams("lat=19.076&lng=72.877&zoom=11.25"))).toEqual({
      lat: 19.076,
      lng: 72.877,
      zoom: 11.25,
    });
  });

  it("rejects partial, non-finite and out-of-range views", () => {
    expect(parseMapView(new URLSearchParams("lat=19&lng=72"))).toBeNull();
    expect(parseMapView(new URLSearchParams("lat=NaN&lng=72&zoom=11"))).toBeNull();
    expect(parseMapView(new URLSearchParams("lat=91&lng=72&zoom=11"))).toBeNull();
  });

  it("only accepts known layers and preserves a view in the URL", () => {
    expect(parseMapLayer("plantability")).toBe("plantability");
    expect(parseMapLayer("<script>")).toBe("hvi");
    const params = new URLSearchParams();
    writeMapView(params, { lat: 19.076, lng: 72.877, zoom: 11.25 });
    expect(parseMapView(params)).toEqual({ lat: 19.076, lng: 72.877, zoom: 11.25 });
  });
});
