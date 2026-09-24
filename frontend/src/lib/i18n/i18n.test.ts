/**
 * Tests for the translation layer (issue #122).
 *
 * The type system already makes a missing key a build error, so these cover
 * what types cannot: that a translation is actually translated, that the
 * placeholders survive, and that locale resolution prefers the URL. The
 * placeholder checks matter most. A dropped `{ward}` compiles perfectly and
 * produces a sentence with a hole in it, in a language the author cannot read.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { DICTIONARIES, LOCALES, LOCALE_META, format, isLocale, lookup, resolveLocale } from "./index";
import en from "./dictionaries/en";

/** Every leaf string in a dictionary, as dotted paths. */
function flatten(node: unknown, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  if (typeof node === "string") {
    out[prefix] = node;
    return out;
  }
  if (node && typeof node === "object") {
    for (const [key, value] of Object.entries(node)) {
      Object.assign(out, flatten(value, prefix ? `${prefix}.${key}` : key));
    }
  }
  return out;
}

const ENGLISH = flatten(en);
const KEYS = Object.keys(ENGLISH).sort();

/** `{placeholders}` in a string, as a sorted list. */
const placeholders = (text: string) =>
  [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

describe("the dictionaries agree on structure", () => {
  it.each(LOCALES)("%s has exactly the English keys, no more and no fewer", (locale) => {
    const keys = Object.keys(flatten(DICTIONARIES[locale])).sort();
    expect(keys).toEqual(KEYS);
  });

  it.each(LOCALES)("%s has no empty strings", (locale) => {
    for (const [key, value] of Object.entries(flatten(DICTIONARIES[locale]))) {
      expect(value.trim(), `${locale}.${key} is blank`).not.toBe("");
    }
  });

  it.each(LOCALES)("%s keeps every placeholder the English copy uses", (locale) => {
    // A dropped {ward} or {date} compiles and leaves a hole in a sentence the
    // author cannot proofread. This is the check that catches it.
    const dict = flatten(DICTIONARIES[locale]);
    for (const key of KEYS) {
      expect(placeholders(dict[key]!), `${locale}.${key} placeholders`).toEqual(
        placeholders(ENGLISH[key]!)
      );
    }
  });
});

describe("the translations are actually translated", () => {
  // Latin-script terms that are correct to leave alone: proper nouns, and the
  // loanwords Mumbai actually uses out loud.
  const KEEPS_LATIN = new Set(["nav.simulator", "footer.sourceCode"]);

  it.each(["mr", "hi"] as const)("%s uses Devanagari for its copy", (locale) => {
    const dict = flatten(DICTIONARIES[locale]);
    const untranslated = KEYS.filter(
      (key) => !KEEPS_LATIN.has(key) && dict[key] === ENGLISH[key]
    );
    expect(untranslated, `still English in ${locale}`).toEqual([]);
  });

  it.each(["mr", "hi"] as const)("%s uses Latin digits, matching what gets interpolated", (locale) => {
    // Every number this interface substitutes at runtime is a Latin numeral,
    // so Devanagari digits in the static copy would produce sentences mixing
    // both scripts.
    for (const [key, value] of Object.entries(flatten(DICTIONARIES[locale]))) {
      expect(/[०-९]/.test(value), `${locale}.${key} has Devanagari digits`).toBe(false);
    }
  });

  it.each(["mr", "hi"] as const)("%s is written in Devanagari, not transliterated", (locale) => {
    // "Dashboard" spelled in Latin script is not a translation. At least most
    // of the copy should be in the script the reader expects.
    const values = Object.entries(flatten(DICTIONARIES[locale]))
      .filter(([key]) => !KEEPS_LATIN.has(key))
      .map(([, value]) => value);
    const devanagari = values.filter((v) => /[ऀ-ॿ]/.test(v));
    expect(devanagari.length / values.length).toBeGreaterThan(0.9);
  });

  it("does not claim the new locales are reviewed", () => {
    // If this ever flips to true it should be because a person reviewed them,
    // and this test is the reminder that flipping it is a claim.
    expect(LOCALE_META.mr.reviewed).toBe(false);
    expect(LOCALE_META.hi.reviewed).toBe(false);
    expect(LOCALE_META.en.reviewed).toBe(true);
  });
});

describe("format", () => {
  it("substitutes named placeholders", () => {
    expect(format("Ward {ward}", { ward: "F/N" })).toBe("Ward F/N");
  });

  it("handles word order differing between languages", () => {
    // English puts the rank first, Marathi and Hindi put the total first.
    const values = { rank: 3, total: 24 };
    expect(format(en.ward.rankOf, values)).toBe("3 of 24");
    expect(format(DICTIONARIES.mr.ward.rankOf, values)).toBe("24 पैकी 3");
    expect(format(DICTIONARIES.hi.ward.rankOf, values)).toBe("24 में से 3");
  });

  it("leaves an unmatched placeholder visible rather than printing undefined", () => {
    // A hole that reads as a bug is better than one that reads as copy.
    expect(format("Ward {ward}", {})).toBe("Ward {ward}");
    expect(format("Ward {ward}", { other: 1 })).not.toContain("undefined");
  });

  it("returns the template untouched when given no values", () => {
    expect(format("no placeholders here")).toBe("no placeholders here");
  });

  it("substitutes every occurrence", () => {
    expect(format("{a} and {a}", { a: "x" })).toBe("x and x");
  });
});

describe("locale resolution", () => {
  it("prefers the URL, so a shared link carries its language", () => {
    expect(resolveLocale("mr", "hi")).toBe("mr");
  });

  it("falls back to the stored preference", () => {
    expect(resolveLocale(null, "hi")).toBe("hi");
  });

  it("falls back to English", () => {
    expect(resolveLocale(null, null)).toBe("en");
  });

  it("ignores a locale it does not have", () => {
    expect(resolveLocale("fr", null)).toBe("en");
    expect(resolveLocale("../etc/passwd", null)).toBe("en");
    expect(resolveLocale(null, "nonsense")).toBe("en");
  });

  it("isLocale rejects non-strings", () => {
    expect(isLocale(undefined)).toBe(false);
    expect(isLocale(42)).toBe(false);
    expect(isLocale("mr")).toBe(true);
  });
});

describe("lookup", () => {
  it("reads a dotted path", () => {
    expect(lookup(en, "nav.dashboard")).toBe("Dashboard");
    expect(lookup(en, "ward.factors.NDVI")).toBe("Green cover");
  });

  it("returns undefined for a path that is not a string", () => {
    expect(lookup(en, "nav")).toBeUndefined();
    expect(lookup(en, "nav.nope")).toBeUndefined();
    expect(lookup(en, "totally.absent.path")).toBeUndefined();
  });
});

describe("the locale store", () => {
  const originalUrl = window.location.href;

  beforeEach(async () => {
    const store = await import("./localeStore");
    store.resetForTests();
    window.localStorage.clear();
  });

  afterEach(() => {
    window.history.replaceState(null, "", originalUrl);
  });

  it("reads the locale out of the query string", async () => {
    window.history.replaceState(null, "", "/dashboard?lang=mr");
    const store = await import("./localeStore");
    store.resetForTests();
    expect(store.getSnapshot()).toBe("mr");
  });

  it("renders the default on the server, where there is no URL", async () => {
    const store = await import("./localeStore");
    expect(store.getServerSnapshot()).toBe("en");
  });

  it("puts the chosen locale in the URL and keeps it out for English", async () => {
    const store = await import("./localeStore");
    store.setLocale("hi");
    expect(new URL(window.location.href).searchParams.get("lang")).toBe("hi");

    // English is the default, so it needs no parameter and should not litter
    // every shared link with one.
    store.setLocale("en");
    expect(new URL(window.location.href).searchParams.get("lang")).toBeNull();
  });

  it("persists the choice", async () => {
    const store = await import("./localeStore");
    store.setLocale("mr");
    expect(window.localStorage.getItem("ucip.locale")).toBe("mr");
  });

  it("notifies subscribers", async () => {
    const store = await import("./localeStore");
    let calls = 0;
    const unsubscribe = store.subscribe(() => {
      calls += 1;
    });
    store.setLocale("hi");
    expect(calls).toBe(1);
    unsubscribe();
  });
});
