/**
 * Issue #40.
 *
 * The point of this suite is the completeness test at the bottom: WARD_AREAS is
 * a hand-maintained lookup, and the map/search read it by ward code. A ward that
 * exists in the pipeline output but has no entry here fails silently as a blank
 * label in the UI, which is exactly the kind of gap nobody notices until a demo.
 * Tying the lookup to the committed GeoJSON makes that a CI failure instead.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { FeatureCollection, Geometry } from "geojson";
import { WARD_AREAS, areasForWard } from "./wardAreas";

const wardsGeo = JSON.parse(
  readFileSync(join(process.cwd(), "public", "wards_hvi.geojson"), "utf8")
) as FeatureCollection<Geometry, { ward_id: string }>;

const wardIdsInData = wardsGeo.features.map((f) => f.properties.ward_id);

describe("areasForWard", () => {
  it("resolves a simple ward code", () => {
    expect(areasForWard("A")).toContain("Colaba");
  });

  it("resolves a split ward code", () => {
    expect(areasForWard("G/N")).toContain("Dharavi");
    expect(areasForWard("M/E")).toContain("Govandi");
  });

  it("returns an empty array for an unknown code rather than undefined", () => {
    // Callers spread this straight into JSX; undefined would throw.
    expect(areasForWard("ZZ")).toEqual([]);
    expect(areasForWard("")).toEqual([]);
  });

  it("is case- and format-sensitive, matching the pipeline's own codes exactly", () => {
    // Documents real behaviour: BMC codes are uppercase with a slash, and the
    // lookup does not normalise. If that ever changes, this test should change
    // with it deliberately.
    expect(areasForWard("g/n")).toEqual([]);
  });
});

describe("WARD_AREAS completeness", () => {
  it("covers all 24 BMC wards", () => {
    expect(Object.keys(WARD_AREAS)).toHaveLength(24);
  });

  it("has an entry for every ward code in the pipeline output", () => {
    const missing = wardIdsInData.filter((id) => !(id in WARD_AREAS));
    expect(missing).toEqual([]);
  });

  it("has no entries for wards that do not exist in the data", () => {
    const orphaned = Object.keys(WARD_AREAS).filter((id) => !wardIdsInData.includes(id));
    expect(orphaned).toEqual([]);
  });

  it("lists at least one named locality per ward", () => {
    for (const [wardId, areas] of Object.entries(WARD_AREAS)) {
      expect(areas.length, `ward ${wardId} has no localities`).toBeGreaterThan(0);
      for (const area of areas) {
        expect(area.trim()).not.toBe("");
      }
    }
  });

  it("does not repeat a locality across two wards", () => {
    // A locality in two wards means one of them is wrong, and the UI would tell
    // a resident their neighbourhood is in a ward it is not.
    const seen = new Map<string, string>();
    const duplicates: string[] = [];
    for (const [wardId, areas] of Object.entries(WARD_AREAS)) {
      for (const area of areas) {
        const prior = seen.get(area);
        if (prior) duplicates.push(`${area} in both ${prior} and ${wardId}`);
        else seen.set(area, wardId);
      }
    }
    expect(duplicates).toEqual([]);
  });
});
