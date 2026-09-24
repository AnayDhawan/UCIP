/**
 * English copy, and the shape every other locale is checked against.
 *
 * This file is the source of truth in both senses: it is what the site says,
 * and its type is what makes a missing Marathi or Hindi key a compile error
 * rather than a silently English string appearing mid-sentence. See
 * `dictionaries/index.ts`.
 *
 * Keys are grouped by where the copy appears, not by word, so that translating
 * a screen means reading one contiguous block with its context intact. A flat
 * alphabetical list of fragments is how translations end up grammatically
 * correct and situationally wrong.
 *
 * `{placeholders}` are substituted by `format()` in `../index.ts`. Word order
 * around them differs between English, Marathi and Hindi, which is the whole
 * reason the placeholder is named rather than positional.
 */

const en = {
  nav: {
    dashboard: "Dashboard",
    cities: "Cities",
    methodology: "Methodology",
    simulator: "Simulator",
    mission: "Mission",
    contribute: "Contribute",
    contact: "Contact",
    siteMenu: "Site menu",
    openMenu: "Open menu",
    closeMenu: "Close menu",
    language: "Language",
    chooseLanguage: "Choose a language",
  },

  dashboard: {
    title: "Heat vulnerability across Mumbai",
    loadingMap: "Loading map…",
    loading: "Loading…",
    dismissHint: "Dismiss hint",
  },

  wardList: {
    heading: "24 wards, ranked by heat vulnerability",
    search: "Find a ward or area…",
    loading: "Loading wards…",
    noResults: "No ward matches that search.",
    follow: "Follow this ward",
    unfollow: "Stop following",
    copyLink: "Copy link",
    linkCopied: "Link copied",
  },

  ward: {
    /** "Ward F/N" */
    label: "Ward {ward}",
    rank: "Rank",
    /** "3rd of 24" style position, kept as one string so word order can change. */
    rankOf: "{rank} of {total}",
    score: "Heat vulnerability index",
    cells: "Grid cells",
    close: "Close",
    /** The seven indicators, as the ward dialog labels them. */
    factors: {
      LST_C: "Land surface temperature",
      NDVI: "Green cover",
      pop_density_km2: "Population density",
      elderly_pct: "Share aged 60 and over",
      slum_pct: "Informal settlement share",
      hospital_dist_m: "Distance to a hospital",
      impervious_pct: "Built-up surface",
    },
  },

  layers: {
    heading: "Map layer",
    hvi: "Heat vulnerability",
    plantable: "Where planting helps",
    ndviChange: "Green cover change",
    temperature: "Surface temperature",
  },

  legend: {
    lower: "Lower",
    higher: "Higher",
    noData: "No data",
  },

  vintage: {
    /** The data's age. Both dates matter and mean different things. */
    refreshed: "Data refreshed {date}",
    imagery: "Imagery from {window}",
    unknown: "Refresh date not yet recorded",
    /** Shown when the API fell back to static files. */
    snapshot: "Serving the last published snapshot",
  },

  caveats: {
    /** Issue #97. Shown on a ward whose score is driven by one indicator. */
    singleFactor:
      "This ward's score is driven mostly by one measure ({factor}), so read it as that measure rather than a combination.",
    /** Issue #87. The ranking is not precise and the interface should not imply it is. */
    rankUncertain:
      "Ranks near the middle of the table overlap. Treat a difference of a few places as no difference.",
    proxy: "This layer is a proxy, not a direct measurement.",
  },

  errors: {
    title: "Something went wrong",
    body: "The page could not be loaded. Reloading usually fixes it.",
    retry: "Try again",
    offline: "You appear to be offline.",
  },

  footer: {
    dataLicence: "Data licences",
    sourceCode: "Source code",
    methodology: "How this is calculated",
  },
} as const;

export default en;
