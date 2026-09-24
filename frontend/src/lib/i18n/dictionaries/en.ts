/**
 * English copy, and the shape every other locale is checked against.
 *
 * This file is the source of truth in both senses: it is what the site says,
 * and its type is what makes a missing Marathi or Hindi key a compile error
 * rather than a silently English string appearing mid-sentence. See
 * `dictionaries/index.ts`.
 *
 * Every key here is read by a component. That is not automatic and it is
 * enforced: the first version of this file held translations for screens that
 * did not exist (a "temperature" layer, a footer, the rank-uncertainty caveats
 * from issues #87 and #97, which the UI does not show), while the components
 * that did exist still had English literals. The types were satisfied and the
 * page was half English. `i18n.test.ts` now fails on any key no source file
 * reads.
 *
 * Keys are grouped by where the copy appears, not by word, so that translating
 * a screen means reading one contiguous block with its context intact.
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
    chooseLanguage: "Choose a language",
    homeLabel: "UCIP home",
    mainNav: "Main",
    mobileNav: "Main mobile",
  },

  dashboard: {
    loadingMap: "Loading map…",
    loading: "Loading…",
    // The hint has a link in the middle of it, so it is three pieces. Word
    // order differs by language, which is why the link text is its own key
    // and each language decides what surrounds it.
    hintLead:
      "Colors rank Mumbai's 24 wards by heat vulnerability. Click any ward, on the map or in the list, to see its breakdown and recommendation. Switch layers top-right, or read the",
    hintLink: "methodology",
    hintTail: ".",
    gotIt: "Got it",
    dismissHint: "Dismiss hint",
  },

  wardList: {
    heading: "24 wards, ranked by heat vulnerability",
    intro: "Click a ward, here or on the map, to open its full profile.",
    search: "Find a ward or area…",
    loading: "Loading wards…",
    noMatch: 'No ward matches "{query}".',
    followingOne: "Following 1 ward",
    followingMany: "Following {n} wards",
    compare: "Compare",
    copyLink: "Copy link",
    copied: "Copied",
    follow: "Follow this ward",
    unfollow: "Stop following",
    followAria: "Follow ward {ward}",
    unfollowAria: "Stop following ward {ward}",
  },

  ward: {
    /** "Ward F/N" */
    label: "Ward {ward}",
    loading: "Loading ward…",
    loadFailed: "Failed to load ward data: {error}",
    mapOf: "Map of {label}",
    boundary: "{label} boundary",
    dialogDescription:
      "Detailed heat vulnerability index, greening data, and recommended interventions for the selected Mumbai ward.",

    header: {
      priority: "Priority {rank} of {total}",
      cells: "{n} grid cells",
      copyEmbed: "Copy embed code",
      copyEmbedAria: "Copy embed code for ward {ward}",
      print: "Print ward brief",
      printAria: "Print ward {ward} brief",
      close: "Close ward details",
    },

    vsCity: "This ward against the city",
    cityValue: "city {value}",
    /** English adds its own ordinal suffix to the rank in code; other languages use the number. */
    rankOf: "{rank} of {total} for heat vulnerability",
    hotterThan: "hotter than {pct}%",
    biggestDriver: "Biggest driver: {factor}.",
    nextDoor: "Next door",
    hottest: "Hottest:",
    coolest: "Coolest:",
    drivesScore: "What drives the score",
    contribHelp:
      "Red pushes this ward's score up, green pushes it down, compared to the city average.",
    recommended: "Recommended interventions",

    /** The eight indicators. Kept identical to FACTOR_LABELS in lib/wardTypes.ts, and tested to be. */
    factors: {
      LST_C: "Land surface temp",
      NDVI: "Green cover (NDVI)",
      pop_density_km2: "Population density",
      elderly_pct: "Elderly %",
      child_pct: "Children under 7 %",
      slum_pct: "Slum index",
      hospital_dist_m: "Hospital distance",
      impervious_pct: "Impervious / built-up",
    },

    /** Sentences describeWard() assembles. Each is a whole template so word order can move. */
    summary: {
      parity:
        "Ward {ward} runs about as warm as the rest of Mumbai across {cells}, averaging {temp} at the surface.",
      offset:
        "Ward {ward} runs about {delta} {direction} than the city average across {cells}, at {temp} of land surface temperature.",
      hotter: "hotter",
      cooler: "cooler",
      oneCell: "its single grid cell",
      manyCells: "its {n} grid cells",
      green:
        "Green cover reads {ndvi} on the NDVI index against {cityNdvi} city-wide, and {built} of the ground is built or paved.",
      people:
        "Around {density} people live per square kilometre, and the nearest hospital averages {distance} away.",
    },
  },

  layers: {
    tabsLabel: "Map layer",
    hvi: {
      label: "Heat vulnerability",
      caption: "How urgently each ward needs cooling, combining heat, people, and access to help.",
    },
    hvi_grid: {
      label: "Heat grid",
      caption:
        "The same index at the 1 km cell it's measured at, before 541 cells are averaged into 24 wards.",
    },
    plantability: {
      label: "Plantability",
      caption: "Where planting trees makes ecological sense, and where cool roofs work better.",
    },
    ndvi_change: {
      label: "Green-cover change",
      caption: "Where vegetation has grown or been lost since the 2016-17 dry season.",
    },
  },

  legend: {
    hviTitle: "Heat Vulnerability Index (0-100)",
    gridTitle: "HVI, 1 km grid (0-100)",
    lessVulnerable: "Less vulnerable",
    mostVulnerable: "Most vulnerable",
    gridNote: "{cells} cells, the same score a ward is averaged from.",
    plantTitle: "Can trees go here?",
    plantYes: "Yes, suitable for planting",
    plantNo: "No, cool roofs instead",
    ndviTitle: "Green cover since 2016-17",
    gained: "Gained vegetation",
    stable: "Stable",
    lost: "Lost vegetation",
  },

  map: {
    ariaLabel: "Mumbai ward heat vulnerability map",
    layerLoadFailed: "Failed to load layer: {error}",
    selectWard: "Select ward {ward}",
    zoomIn: "Zoom in",
    zoomOut: "Zoom out",
    findMyWard: "Find my ward",
    finding: "Finding your ward…",
    findMyWardTitle: "Find my ward: use your location",
    exitFullscreen: "Exit fullscreen",
    viewFullscreen: "View map fullscreen",
    exitFullscreenTitle: "Exit fullscreen (Esc)",
    viewFullscreenTitle: "View fullscreen",
  },

  /** Why "find my ward" failed, keyed by LocateFailureKind in lib/findWard.ts. */
  locate: {
    unsupported: "Location isn't available in this browser.",
    denied: "Location permission was denied. You can pick your ward from the list instead.",
    unavailable: "Your location couldn't be determined right now.",
    timeout: "Finding your location timed out. Try again.",
    outside: "You're outside the 24 BMC wards, so there's no ward here.",
    lookup: "Couldn't look up your ward. Try again in a moment.",
  },

  compare: {
    heading: "Ward comparison",
    description: "Comparing followed wards. This view is saved in the URL.",
    loadFailed: "Failed to load wards: {error}",
    measure: "Measure",
    hvi: "HVI",
    cityRank: "City rank",
    recommendations: "Recommendations",
    notAvailable: "n/a",
  },

  trend: {
    since: "Since {year}",
    surfaceTemp: "Surface temperature",
    greenCover: "Green cover",
    lstAria: "Dry-season land surface temperature",
    ndviAria: "Dry-season NDVI",
    sparkAria: "{label}: {first} in {firstYear} to {last} in {lastYear}",
    noTrend: "no detected trend ({value})",
    perDecade: "{value} {unit}/decade",
    warming: "warming",
    cooling: "cooling",
    greening: "greening",
    losingGreen: "losing green",
    footSignificant:
      "Least-squares slope over {n} dry seasons. It describes the observed period, not a forecast.",
    footFlat:
      "{n} dry seasons of Landsat show no trend distinguishable from year-to-year variation in this ward. The sparklines are the real measurements; the slope is shown for completeness, not as a finding.",
  },

  vintage: {
    refreshed: "Data refreshed {date}",
    withWindow: "Data refreshed {date} · computed from imagery captured {window}",
  },

  common: {
    close: "Close",
  },

  theme: {
    label: "Color theme",
    light: "Light",
    dark: "Dark",
    auto: "Auto",
  },

  errors: {
    title: "Something went wrong",
    body: "The dashboard hit an unexpected error. Try reloading, if it keeps happening let us know.",
    retry: "Try again",
  },

  /**
   * Recommendation text arrives from the pipeline as English strings, so these
   * are lookups keyed by that exact text. A string with no entry here falls
   * back to the English the pipeline sent, which is the right failure: a new
   * rule shows in English until someone translates it, and never disappears.
   * Citations are deliberately absent. They are paper titles and author names.
   */
  recs: {
    interventions: {
      "Native tree planting + green corridors": "Native tree planting + green corridors",
      "Cool roofs + reflective pavements + cooling centres":
        "Cool roofs + reflective pavements + cooling centres",
      "Rain gardens + water-sensitive urban design (WSUD)":
        "Rain gardens + water-sensitive urban design (WSUD)",
      "Pocket parks": "Pocket parks",
      "Cooling centres, priority siting": "Cooling centres, priority siting",
    },
    citations: {
      "Methodology proxy: WorldCover water-distance < 500m (no dedicated hydrology layer in P0)":
        "Methodology proxy: WorldCover water-distance < 500m (no dedicated hydrology layer in P0)",
    },
    rationales: {
      "High vulnerability, low canopy, ecologically suitable for restoration":
        "High vulnerability, low canopy, ecologically suitable for restoration",
      "High vulnerability, low canopy, but native-grassland/built-up cell: afforestation would backfire ecologically":
        "High vulnerability, low canopy, but native-grassland/built-up cell: afforestation would backfire ecologically",
      "Highly impervious cell near mapped water/wetland: runoff and heat compound risk":
        "Highly impervious cell near mapped water/wetland: runoff and heat compound risk",
      "High population density with little existing green/open space":
        "High population density with little existing green/open space",
      "High elderly share combined with poor hospital access":
        "High elderly share combined with poor hospital access",
    },
  },
} as const;

export default en;
