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
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FACTOR_LABELS } from "@/lib/wardTypes";
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
  const KEEPS_LATIN = new Set(["nav.simulator", "compare.hvi"]);

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
    expect(format(en.ward.rankOf, values)).toBe("3 of 24 for heat vulnerability");
    expect(format(DICTIONARIES.mr.ward.rankOf, values)).toBe("उष्णतेच्या धोक्यात 24 पैकी 3");
    expect(format(DICTIONARIES.hi.ward.rankOf, values)).toBe("गर्मी के खतरे में 24 में से 3");
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
    expect(lookup(en, "ward.factors.NDVI")).toBe("Green cover (NDVI)");
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


/**
 * The tests that would have caught the first version of this feature.
 *
 * The structural tests above prove that every dictionary has every key. They
 * say nothing about whether a component reads any of them. The first pass
 * shipped dictionaries with translations for screens that did not exist, while
 * the screens that did exist still had English string literals in the JSX. The
 * type checker was satisfied, the build passed, 33 tests passed, and the page
 * was half English. Nothing in the suite looked at the page.
 */
describe("the dictionary is actually used", () => {
  /** Every source file the site ships, excluding the dictionaries and the tests. */
  function sourceFiles(dir: string): string[] {
    const out: string[] = [];
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      if (statSync(full).isDirectory()) {
        if (name === "dictionaries" || name === "node_modules") continue;
        out.push(...sourceFiles(full));
      } else if (/\.(ts|tsx)$/.test(name) && !/\.test\./.test(name)) {
        out.push(full);
      }
    }
    return out;
  }

  const files = sourceFiles(join(process.cwd(), "src")).map((path) => readFileSync(path, "utf8"));

  // Read through a computed key (t.locate[err.kind], t.ward.factors[key],
  // dict.recs[group]), so the leaf name never appears in source. Checked as a
  // group below instead.
  const DYNAMIC = ["ward.factors.", "locate.", "recs."];

  it("every key is read by a component", () => {
    const unused: string[] = [];
    for (const key of KEYS) {
      if (DYNAMIC.some((prefix) => key.startsWith(prefix))) continue;
      const parts = key.split(".");
      const section = parts[0]!;
      const leaf = parts[parts.length - 1]!;
      // Some file has to mention both the section and the leaf. Not proof that
      // the two are connected, but a key nothing mentions fails, which is the
      // failure that actually happened.
      // A key read as `t.nav[item.key]` never spells the leaf as a property, but
      // it does appear as the value the table looks it up by: `key: "dashboard"`.
      const used = files.some(
        (src) =>
          src.includes(`t.${section}`) &&
          (new RegExp(`[.\\[]\\s*["']?${leaf}\\b`).test(src) ||
            new RegExp(`key:\\s*["']${leaf}["']`).test(src))
      );
      if (!used) unused.push(key);
    }
    expect(unused, "dictionary keys no component reads").toEqual([]);
  });

  it("the dynamically read groups are each read somewhere", () => {
    expect(files.some((src) => /t\.locate\[/.test(src))).toBe(true);
    expect(files.some((src) => /t\.ward\.factors\[/.test(src))).toBe(true);
    expect(files.some((src) => /\.recs\[/.test(src))).toBe(true);
  });

  it("the English factor labels are the ones the rest of the site already uses", () => {
    // FACTOR_LABELS still feeds the methodology page, and two copies of a label
    // is how English drifts between screens.
    expect(en.ward.factors).toEqual(FACTOR_LABELS);
  });

  it("every layer the map can show has a label and a caption", () => {
    for (const id of ["hvi", "hvi_grid", "plantability", "ndvi_change"] as const) {
      for (const locale of LOCALES) {
        expect(DICTIONARIES[locale].layers[id].label.trim(), `${locale}.${id}`).not.toBe("");
        expect(DICTIONARIES[locale].layers[id].caption.trim(), `${locale}.${id}`).not.toBe("");
      }
    }
  });

  it("every locate failure and every recommendation the pipeline can emit is translated", () => {
    for (const locale of ["mr", "hi"] as const) {
      const d = DICTIONARIES[locale];
      for (const [kind, text] of Object.entries(d.locate)) {
        expect(text, `${locale}.locate.${kind}`).not.toBe((en.locate as Record<string, string>)[kind]);
      }
      for (const [group, entries] of Object.entries(d.recs)) {
        for (const [english, local] of Object.entries(entries as Record<string, string>)) {
          expect(local, `${locale}.recs.${group}: ${english.slice(0, 40)}`).not.toBe(english);
        }
      }
    }
  });
});
