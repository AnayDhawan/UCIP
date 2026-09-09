import { afterEach, describe, expect, it, vi } from "vitest";
import {
  findMyWard,
  LOCATE_ERROR_MESSAGE,
  lookupWard,
  requestLocation,
} from "./findWard";
import type { LocateFailureKind } from "./findWard";

/**
 * Temporarily replaces navigator.geolocation. jsdom has no geolocation at all,
 * so every stub must be configurable for the next stub (or the delete below)
 * to replace it.
 */
function stubGeolocation(impl: Geolocation["getCurrentPosition"]): () => void {
  const original = Object.getOwnPropertyDescriptor(navigator, "geolocation");
  Object.defineProperty(navigator, "geolocation", {
    value: { getCurrentPosition: impl },
    configurable: true,
  });
  return () => {
    if (original) Object.defineProperty(navigator, "geolocation", original);
    else delete (navigator as { geolocation?: unknown }).geolocation;
  };
}

/** Removes any geolocation stub so the "no API at all" state is real. */
function removeGeolocationStub() {
  const descriptor = Object.getOwnPropertyDescriptor(navigator, "geolocation");
  if (descriptor) delete (navigator as { geolocation?: unknown }).geolocation;
}

function positionError(code: number): GeolocationPositionError {
  // GeolocationPositionError is not constructible in jsdom; its shape is what
  // matters (the module reads only `code`).
  return { code, PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as unknown as GeolocationPositionError;
}

function okPosition(lat = 19.076, lng = 72.877): GeolocationPosition {
  return {
    coords: {
      latitude: lat,
      longitude: lng,
      accuracy: 20,
      altitude: null,
      altitudeAccuracy: null,
      heading: null,
      speed: null,
    },
    timestamp: Date.now(),
  } as GeolocationPosition;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("requestLocation", () => {
  it("resolves coordinates when the browser returns a fix", async () => {
    const restore = stubGeolocation((onOk) => onOk(okPosition(19.076, 72.877)));
    try {
      await expect(requestLocation()).resolves.toEqual({ lat: 19.076, lng: 72.877 });
    } finally {
      restore();
    }
  });

  it("fails with kind 'unsupported' when there is no geolocation API", async () => {
    removeGeolocationStub(); // jsdom ships no geolocation; exercise that state.
    await expect(requestLocation()).rejects.toEqual({ kind: "unsupported" });
  });

  it("maps each position-error code to the right failure kind", async () => {
    const expectations: Array<[number, LocateFailureKind]> = [
      [1, "denied"],
      [2, "unavailable"],
      [3, "timeout"],
    ];
    for (const [code, kind] of expectations) {
      removeGeolocationStub();
      const restore = stubGeolocation((_ok, onErr) => onErr(positionError(code)));
      try {
        await expect(requestLocation()).rejects.toEqual({ kind });
      } finally {
        restore();
      }
    }
  });
});

describe("lookupWard", () => {
  it("resolves the ward id from a 200 response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ ward: { ward_id: "L" } }), { status: 200 })
      )
    );
    await expect(lookupWard(19.076, 72.877)).resolves.toEqual({ ward_id: "L" });
    const url = String(vi.mocked(fetch).mock.calls[0]?.[0]);
    expect(url).toContain("/api/v1/lookup?lat=19.076&lon=72.877");
  });

  it("fails with kind 'outside' on a 404", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 404 })));
    await expect(lookupWard(0, 0)).rejects.toEqual({ kind: "outside" });
  });

  it("fails with kind 'lookup' on other errors and on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 503 })));
    await expect(lookupWard(19.076, 72.877)).rejects.toEqual({ kind: "lookup" });
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(lookupWard(19.076, 72.877)).rejects.toEqual({ kind: "lookup" });
  });
});

describe("findMyWard", () => {
  it("runs geolocation then lookup and returns the ward id", async () => {
    const restore = stubGeolocation((onOk) => onOk(okPosition(19.076, 72.877)));
    try {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(
          new Response(JSON.stringify({ ward: { ward_id: "L" } }), { status: 200 })
        )
      );
      await expect(findMyWard()).resolves.toBe("L");
    } finally {
      restore();
    }
  });

  it("propagates a permission denial without calling the lookup", async () => {
    const restore = stubGeolocation((_ok, onErr) => onErr(positionError(1)));
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    try {
      await expect(findMyWard()).rejects.toEqual({ kind: "denied" });
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      restore();
    }
  });
});

describe("LOCATE_ERROR_MESSAGE", () => {
  it("has copy for every failure kind", () => {
    const kinds: LocateFailureKind[] = [
      "unsupported",
      "denied",
      "unavailable",
      "timeout",
      "outside",
      "lookup",
    ];
    for (const kind of kinds) {
      expect(LOCATE_ERROR_MESSAGE[kind]).toBeTruthy();
    }
  });
});
