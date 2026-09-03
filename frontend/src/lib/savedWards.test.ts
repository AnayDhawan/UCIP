import { describe, it, expect, vi, afterEach } from "vitest";
import {
  parseWardParam,
  serializeWardParam,
  toggleWard,
  readStoredWards,
  writeStoredWards,
} from "./savedWards";

afterEach(() => {
  vi.restoreAllMocks();
  try {
    window.localStorage.clear();
  } catch {
    // ignored
  }
});

describe("parseWardParam", () => {
  it("parses a comma-separated list", () => {
    expect(parseWardParam("F/N,G/S,A")).toEqual(["F/N", "G/S", "A"]);
  });

  it("returns an empty list for null or empty input", () => {
    expect(parseWardParam(null)).toEqual([]);
    expect(parseWardParam("")).toEqual([]);
  });

  it("trims whitespace and uppercases", () => {
    expect(parseWardParam(" f/n , g/s ")).toEqual(["F/N", "G/S"]);
  });

  it("de-duplicates while preserving order", () => {
    expect(parseWardParam("F/N,G/S,F/N")).toEqual(["F/N", "G/S"]);
  });

  it("discards anything that is not a BMC ward code", () => {
    // These values reach React keys, map lookups and eventually the DOM, so the
    // URL is treated as untrusted input rather than as configuration.
    expect(parseWardParam("F/N,<script>,G/S")).toEqual(["F/N", "G/S"]);
    expect(parseWardParam("../../etc/passwd")).toEqual([]);
    expect(parseWardParam("TOOLONG")).toEqual([]);
    expect(parseWardParam("F/N/X")).toEqual([]);
    expect(parseWardParam("1,2,3")).toEqual([]);
  });

  it("caps the list so a hostile link cannot blow up the panel", () => {
    const huge = Array.from({ length: 500 }, (_, i) => `A${i}`).join(",");
    expect(parseWardParam(huge).length).toBeLessThanOrEqual(24);
  });

  it("round-trips through serializeWardParam", () => {
    const ids = ["F/N", "G/S", "R/C"];
    expect(parseWardParam(serializeWardParam(ids))).toEqual(ids);
  });
});

describe("toggleWard", () => {
  it("adds a ward that is not tracked", () => {
    expect(toggleWard(["F/N"], "G/S")).toEqual(["F/N", "G/S"]);
  });

  it("removes a ward that is already tracked", () => {
    expect(toggleWard(["F/N", "G/S"], "F/N")).toEqual(["G/S"]);
  });

  it("does not mutate the input array", () => {
    const original = ["F/N"];
    toggleWard(original, "G/S");
    expect(original).toEqual(["F/N"]);
  });

  it("toggling twice returns to the original set", () => {
    expect(toggleWard(toggleWard(["F/N"], "G/S"), "G/S")).toEqual(["F/N"]);
  });
});

describe("localStorage round-trip", () => {
  it("persists and reads back a set", () => {
    writeStoredWards(["F/N", "G/S"]);
    expect(readStoredWards()).toEqual(["F/N", "G/S"]);
  });

  it("clears storage when the set empties", () => {
    writeStoredWards(["F/N"]);
    writeStoredWards([]);
    expect(readStoredWards()).toEqual([]);
  });

  it("returns an empty set rather than throwing when storage is blocked", () => {
    // Private-browsing modes and "block site data" settings make localStorage
    // access throw outright. The dashboard must still render.
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("SecurityError");
    });
    expect(() => readStoredWards()).not.toThrow();
    expect(readStoredWards()).toEqual([]);
  });

  it("swallows write failures", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });
    expect(() => writeStoredWards(["F/N"])).not.toThrow();
  });

  it("sanitises whatever is already in storage", () => {
    // Storage is as untrusted as the URL: an older build, or another tab, may
    // have written something this version would not.
    window.localStorage.setItem("ucip-tracked-wards", "F/N,<img src=x>,G/S");
    expect(readStoredWards()).toEqual(["F/N", "G/S"]);
  });
});
