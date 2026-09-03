/**
 * Issue #38.
 *
 * citations.ts is the single source of truth behind the methodology table, the
 * landing page citation wall, and the inline chips on ward cards. A typo'd id or
 * a malformed DOI fails silently in the UI as a dead link or a missing citation,
 * which on a project whose entire pitch is "every weight cites a paper" is worse
 * than a crash.
 */

import { describe, it, expect } from "vitest";
import {
  CITATIONS,
  CITATION_CATEGORY_LABELS,
  getCitation,
  doiUrl,
  matchCitationFromText,
} from "./citations";

describe("getCitation", () => {
  it("resolves a known id", () => {
    const reid = getCitation("reid2009");
    expect(reid).toBeDefined();
    expect(reid!.authors).toBe("Reid et al. 2009");
    expect(reid!.year).toBe(2009);
  });

  it("returns undefined for an unknown id rather than throwing", () => {
    expect(getCitation("nosuchpaper2099")).toBeUndefined();
    expect(getCitation("")).toBeUndefined();
  });

  it("does not resolve inherited Object properties as citations", () => {
    // The lookup is built with Object.fromEntries, so "constructor" and
    // "toString" would resolve to functions on a naive implementation.
    expect(getCitation("constructor")).toBeUndefined();
    expect(getCitation("toString")).toBeUndefined();
    expect(getCitation("__proto__")).toBeUndefined();
  });

  it("resolves every id present in CITATIONS", () => {
    for (const entry of CITATIONS) {
      expect(getCitation(entry.id), `id ${entry.id} does not resolve`).toBe(entry);
    }
  });
});

describe("doiUrl", () => {
  it("builds a resolver URL from a bare DOI", () => {
    expect(doiUrl("10.1289/ehp.0900683")).toBe("https://doi.org/10.1289/ehp.0900683");
  });

  it("preserves DOIs containing slashes, dots and hyphens", () => {
    expect(doiUrl("10.1016/j.landurbplan.2010.05.006")).toBe(
      "https://doi.org/10.1016/j.landurbplan.2010.05.006"
    );
    expect(doiUrl("10.1088/1748-9326/9/5/055002")).toBe(
      "https://doi.org/10.1088/1748-9326/9/5/055002"
    );
  });

  it("produces a parseable absolute URL for every citation in the table", () => {
    for (const entry of CITATIONS) {
      const url = doiUrl(entry.doi);
      expect(() => new URL(url), `bad DOI URL for ${entry.id}`).not.toThrow();
      expect(url.startsWith("https://doi.org/10.")).toBe(true);
    }
  });
});

describe("matchCitationFromText", () => {
  it("matches the free-text citation strings the pipeline actually emits", () => {
    // These are real strings from pipeline/06_nbs.py's recommendation output.
    expect(matchCitationFromText("Ziter et al. 2019, PNAS")!.id).toBe("ziter2019");
    expect(
      matchCitationFromText("Veldman et al. 2019, Science (response to Bastin 2019)")!.id
    ).toBe("veldman2019");
    expect(matchCitationFromText("Santamouris 2014, Solar Energy")!.id).toBe("santamouris2014");
  });

  it("is case-insensitive", () => {
    expect(matchCitationFromText("ZITER ET AL. 2019")!.id).toBe("ziter2019");
    expect(matchCitationFromText("bowler et al. 2010")!.id).toBe("bowler2010");
  });

  it("prefers the first listed pattern when a string names two papers", () => {
    // The Veldman entry is literally "Veldman ... (response to Bastin 2019)", so
    // ordering in the crosswalk is load-bearing: it must resolve to Veldman, the
    // paper making the claim, not Bastin, the paper being answered.
    expect(
      matchCitationFromText("Veldman et al. 2019, Science (response to Bastin 2019)")!.id
    ).toBe("veldman2019");
  });

  it("returns undefined for text naming no known paper", () => {
    expect(matchCitationFromText("Local municipal guidance, undated")).toBeUndefined();
    expect(matchCitationFromText("")).toBeUndefined();
  });

  it("does not false-positive on unrelated prose", () => {
    expect(matchCitationFromText("Plant native trees along the corridor")).toBeUndefined();
    expect(matchCitationFromText("Cool roofs on municipal buildings")).toBeUndefined();
  });
});

describe("the citation table itself", () => {
  it("has unique ids", () => {
    const ids = CITATIONS.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("has unique DOIs", () => {
    const dois = CITATIONS.map((c) => c.doi);
    expect(new Set(dois).size).toBe(dois.length);
  });

  it("gives every entry a non-empty usage note", () => {
    // "What does this paper justify" is the column that makes the citation wall
    // meaningful rather than decorative.
    for (const entry of CITATIONS) {
      expect(entry.usage.trim(), `${entry.id} has no usage note`).not.toBe("");
    }
  });

  it("uses only categories that have a display label", () => {
    for (const entry of CITATIONS) {
      expect(CITATION_CATEGORY_LABELS[entry.category]).toBeDefined();
    }
  });

  it("marks every entry as DOI-verified", () => {
    // All DOIs were checked live on 2026-07-12. A new entry landing unverified
    // should be a deliberate, visible choice.
    const unverified = CITATIONS.filter((c) => !c.verified).map((c) => c.id);
    expect(unverified).toEqual([]);
  });
});
