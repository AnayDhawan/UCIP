/**
 * Renders the ward detail in each language and looks for English that should
 * not be there (issue #122).
 *
 * The first version of the i18n work translated the navigation and half the
 * ward list and reported the dashboard as done. The dictionary tests passed
 * because they only look at dictionaries. This looks at what a reader gets.
 *
 * It is a spot check on one component, not a proof about the whole app. The
 * broader guarantee is the "every key is read" test in lib/i18n, which fails on
 * a key nothing uses; this covers the opposite mistake, an English literal that
 * never had a key at all.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import WardDetail from "./WardDetail";
import { LocaleProvider } from "@/lib/i18n/LocaleProvider";
import { DICTIONARIES, format } from "@/lib/i18n";
import { resetForTests } from "@/lib/i18n/localeStore";
import type { NbsRec, WardProps } from "@/lib/wardTypes";
import type { CityProfile, WardProfile } from "@/lib/wardProfile";

const city: CityProfile = {
  hvi_mean: 50,
  LST_C: 32.4,
  NDVI: 0.37,
  pop_density_km2: 27500,
  elderly_pct: 4.9,
  child_pct: 9.5,
  slum_pct: 6,
  hospital_dist_m: 1400,
  impervious_pct: 39,
};

const profile: WardProfile = {
  ward_id: "F/N",
  ward_gid: 7,
  hvi: 71.2,
  rank: 3,
  n_cells: 22,
  percentile: 87,
  LST_C: 34.1,
  LST_C_delta_city: 1.7,
  NDVI: 0.28,
  NDVI_delta_city: -0.09,
  pop_density_km2: 41250,
  pop_density_km2_delta_city: 13750,
  elderly_pct: 5.6,
  elderly_pct_delta_city: 0.7,
  child_pct: 9.9,
  child_pct_delta_city: 0.4,
  slum_pct: 10,
  slum_pct_delta_city: 4,
  hospital_dist_m: 820,
  hospital_dist_m_delta_city: -580,
  impervious_pct: 73,
  impervious_pct_delta_city: 34,
  top_driver: "LST_C",
  top_driver_contrib: 0.31,
  neighbours: ["G/N"],
  coolest_neighbour: { ward_id: "F/S", hvi: 60.1 },
  hottest_neighbour: { ward_id: "G/N", hvi: 74.3 },
};

const ward = {
  ward_id: "F/N",
  ward_gid: 7,
  HVI: 71.2,
  rank: 3,
  n_cells: 22,
  contrib_LST_C: 0.2,
  contrib_NDVI: 0.1,
  contrib_pop_density_km2: 0.1,
  contrib_elderly_pct: 0.05,
  contrib_child_pct: 0.01,
  contrib_slum_pct: 0.02,
  contrib_hospital_dist_m: -0.05,
  contrib_impervious_pct: 0.15,
} as WardProps;

const recs: NbsRec[] = [
  {
    ward_id: "F/N",
    intervention: "Pocket parks",
    rationale: "High population density with little existing green/open space",
    citation: "C40 Urban Cooling Toolbox",
    priority: 1,
    cell_count: 4,
  },
];

function renderIn(locale: "en" | "mr" | "hi") {
  window.history.replaceState(null, "", locale === "en" ? "/" : `/?lang=${locale}`);
  resetForTests();
  return render(
    <LocaleProvider>
      <WardDetail
        ward={ward}
        profile={profile}
        city={city}
        recs={recs}
        totalWards={24}
        onSelectWard={() => {}}
      />
    </LocaleProvider>
  );
}

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  cleanup();
  window.history.replaceState(null, "", "/");
  resetForTests();
});

/** English strings that must not survive in a translated render. */
function englishUi() {
  const en = DICTIONARIES.en;
  return [
    en.ward.vsCity,
    en.ward.nextDoor,
    en.ward.hottest,
    en.ward.coolest,
    en.ward.drivesScore,
    en.ward.contribHelp,
    en.ward.recommended,
    "runs about",
    "for heat vulnerability",
    "Biggest driver",
    "hotter than",
    "Pocket parks",
    "little existing green",
  ];
}

describe.each(["mr", "hi"] as const)("WardDetail in %s", (locale) => {
  it("contains none of the English interface copy", () => {
    const { container } = renderIn(locale);
    const text = container.textContent ?? "";
    const leaked = englishUi().filter((phrase) => text.includes(phrase));
    expect(leaked, `English left on the page in ${locale}`).toEqual([]);
  });

  it("shows the translated headings", () => {
    const d = DICTIONARIES[locale];
    const text = renderIn(locale).container.textContent ?? "";
    for (const heading of [d.ward.vsCity, d.ward.nextDoor, d.ward.drivesScore, d.ward.recommended]) {
      expect(text).toContain(heading);
    }
  });

  it("translates the sentences it assembles, with the numbers intact", () => {
    const d = DICTIONARIES[locale];
    const text = renderIn(locale).container.textContent ?? "";
    expect(text).toContain(format(d.ward.rankOf, { rank: 3, total: 24 }));
    expect(text).toContain(format(d.ward.hotterThan, { pct: 87 }));
    // The ward code stays in Latin script whatever the language: it is what is
    // printed on every BMC sign.
    expect(text).toContain(format(d.ward.label, { ward: "G/N" }));
  });

  it("translates the recommendation text the pipeline sends in English", () => {
    const d = DICTIONARIES[locale];
    const text = renderIn(locale).container.textContent ?? "";
    expect(text).toContain(d.recs.interventions["Pocket parks"]);
    expect(text).toContain(d.recs.rationales["High population density with little existing green/open space"]);
  });

  it("leaves the citation alone, since it is an author and a paper title", () => {
    expect(renderIn(locale).container.textContent ?? "").toContain("C40");
  });

  it("labels the new child-share indicator in the reader's language", () => {
    const d = DICTIONARIES[locale];
    expect(renderIn(locale).container.textContent ?? "").toContain(d.ward.factors.child_pct);
  });
});

describe("WardDetail in English", () => {
  it("still reads exactly as it did before the dictionary existed", () => {
    const text = renderIn("en").container.textContent ?? "";
    expect(text).toContain("This ward against the city");
    expect(text).toContain("3rd of 24 for heat vulnerability");
    expect(text).toContain("hotter than 87%");
    expect(text).toContain("Pocket parks");
    expect(text).toContain("Children under 7 %");
  });
});
