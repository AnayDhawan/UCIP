import { describe, expect, it } from "vitest";
import {
  formatCompositeWindow,
  formatRunDate,
  formatWindowDate,
} from "./runLog";

describe("formatRunDate", () => {
  it("formats a UTC timestamp as a plain date, in UTC", () => {
    // +00:00 and Z are the two spellings Python's datetime.isoformat() emits.
    expect(formatRunDate("2026-09-03T12:40:11+00:00")).toBe("3 Sep 2026");
    expect(formatRunDate("2026-09-03T23:59:59Z")).toBe("3 Sep 2026");
  });

  it("does not shift a late-UTC timestamp into another day", () => {
    // Regression guard for the timeZone: "UTC" choice — rendered in IST this
    // instant would be 4 Sep.
    expect(formatRunDate("2026-09-03T20:00:00Z")).toBe("3 Sep 2026");
  });

  it("returns null for missing or unparseable input", () => {
    expect(formatRunDate(null)).toBeNull();
    expect(formatRunDate(undefined)).toBeNull();
    expect(formatRunDate("")).toBeNull();
    expect(formatRunDate("not a date")).toBeNull();
  });
});

describe("formatWindowDate", () => {
  it("formats date-only bounds", () => {
    expect(formatWindowDate("2025-11-01")).toBe("1 Nov 2025");
    expect(formatWindowDate("2026-02-28")).toBe("28 Feb 2026");
    expect(formatWindowDate("2024-02-29")).toBe("29 Feb 2024");
  });

  it("returns null for missing or unparseable input", () => {
    expect(formatWindowDate(null)).toBeNull();
    expect(formatWindowDate("2026-13-01")).toBeNull();
  });
});

describe("formatCompositeWindow", () => {
  it("renders the range with an en dash", () => {
    expect(
      formatCompositeWindow({ start: "2025-11-01", end: "2026-02-28" })
    ).toBe("1 Nov 2025 – 28 Feb 2026");
  });

  it("returns null when either bound is missing or invalid", () => {
    expect(formatCompositeWindow(null)).toBeNull();
    expect(formatCompositeWindow(undefined)).toBeNull();
    expect(formatCompositeWindow({ start: "", end: "2026-02-28" })).toBeNull();
    expect(formatCompositeWindow({ start: "2025-11-01", end: "nope" })).toBeNull();
  });
});
