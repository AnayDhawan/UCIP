/**
 * Single source of truth for UCIP's citations, transcribed from `docs/references.md`
 * (verified 2026-07-12). `Citation.tsx` and `WardPanel.tsx` both read from this file
 * so the methodology table, the landing page's citation wall, and inline ward-card
 * citations never drift out of sync again.
 */

export type CitationCategory = "vulnerability-index" | "plantability-filter" | "cooling-coefficients";

export type CitationEntry = {
  id: string;
  authors: string;
  year: number;
  venue: string;
  doi: string;
  verified: boolean;
  usage: string;
  category: CitationCategory;
};

export const CITATION_CATEGORY_LABELS: Record<CitationCategory, string> = {
  "vulnerability-index": "Vulnerability index",
  "plantability-filter": "Plantability filter",
  "cooling-coefficients": "Cooling coefficients",
};

export const CITATIONS: CitationEntry[] = [
  {
    id: "reid2009",
    authors: "Reid et al. 2009",
    year: 2009,
    venue: "Environ. Health Perspect. 117(11):1730-1736",
    doi: "10.1289/ehp.0900683",
    verified: true,
    usage: "PCA-derived HVI weights (data, not guesses)",
    category: "vulnerability-index",
  },
  {
    id: "knowlton2014",
    authors: "Knowlton et al. 2014",
    year: 2014,
    venue: "IJERPH 11(4):3473-3492",
    doi: "10.3390/ijerph110403473",
    verified: true,
    usage: "Local credibility; first Heat Action Plan in South Asia",
    category: "vulnerability-index",
  },
  {
    id: "azhar2017",
    authors: "Azhar et al. 2017 (RAND India HVI)",
    year: 2017,
    venue: "IJERPH 14(4):357",
    doi: "10.3390/ijerph14040357",
    verified: true,
    usage: "India-wide district HVI precedent; UCIP goes ward-level",
    category: "vulnerability-index",
  },
  {
    id: "bastin2019",
    authors: "Bastin et al. 2019",
    year: 2019,
    venue: "Science 365(6448):76-79",
    doi: "10.1126/science.aax0848",
    verified: true,
    usage: "Global canopy restoration potential; where trees can go",
    category: "plantability-filter",
  },
  {
    id: "veldman2019",
    authors: "Veldman et al. 2019",
    year: 2019,
    venue: "Science 366(6463):eaay7976",
    doi: "10.1126/science.aay7976",
    verified: true,
    usage: "Don't afforest grasslands or savannas — powers the plantability filter",
    category: "plantability-filter",
  },
  {
    id: "friedlingstein2019",
    authors: "Friedlingstein et al. 2019",
    year: 2019,
    venue: "Science 366(6463):eaay8060",
    doi: "10.1126/science.aay8060",
    verified: true,
    usage: "Restoration estimate is inconsistent with carbon-cycle dynamics; trees are not a substitute for cutting emissions",
    category: "plantability-filter",
  },
  {
    id: "lewis2019",
    authors: "Lewis et al. 2019",
    year: 2019,
    venue: "Science 366(6463):eaaz0388",
    doi: "10.1126/science.aaz0388",
    verified: true,
    usage: "Regrowth mostly replaces previously-lost carbon, not new sequestration",
    category: "plantability-filter",
  },
  {
    id: "ziter2019",
    authors: "Ziter et al. 2019",
    year: 2019,
    venue: "PNAS 116(15):7575-7580",
    doi: "10.1073/pnas.1817561116",
    verified: true,
    usage: "Canopy percent to LST reduction coefficients (simulator and NBS impact)",
    category: "cooling-coefficients",
  },
  {
    id: "li2014",
    authors: "Li, Bou-Zeid & Oppenheimer 2014",
    year: 2014,
    venue: "Environ. Res. Lett. 9(5):055002",
    doi: "10.1088/1748-9326/9/5/055002",
    verified: true,
    usage: "Cool-roof fraction to UHI reduction, structural support for a linear term",
    category: "cooling-coefficients",
  },
  {
    id: "santamouris2014",
    authors: "Santamouris 2014",
    year: 2014,
    venue: "Solar Energy 103:682-703",
    doi: "10.1016/j.solener.2012.07.003",
    verified: true,
    usage: "Albedo to peak-temperature coefficient (~0.6-2.3K per +0.1 albedo)",
    category: "cooling-coefficients",
  },
];

const CITATIONS_BY_ID: Record<string, CitationEntry> = Object.fromEntries(
  CITATIONS.map((c) => [c.id, c])
);

export function getCitation(id: string): CitationEntry | undefined {
  return CITATIONS_BY_ID[id];
}

export function doiUrl(doi: string): string {
  return `https://doi.org/${doi}`;
}

/**
 * `pipeline/06_nbs.py` emits free-text citation strings on each NBS recommendation
 * (e.g. "Veldman et al. 2019, Science (response to Bastin 2019)"), not a stable id.
 * This crosswalk lets WardPanel render a proper Citation chip from that text without
 * changing the pipeline. It's intentionally a small, explicit map, not fuzzy matching —
 * a durable fix belongs in the pipeline (see plan's "what's left" notes), this is a
 * frontend-only bridge.
 */
const CITATION_TEXT_TO_ID: [pattern: RegExp, id: string][] = [
  [/veldman/i, "veldman2019"],
  [/bastin/i, "bastin2019"],
  [/friedlingstein/i, "friedlingstein2019"],
  [/lewis/i, "lewis2019"],
  [/ziter/i, "ziter2019"],
  [/santamouris/i, "santamouris2014"],
  [/li.*bou-zeid|bou-zeid/i, "li2014"],
  [/reid/i, "reid2009"],
  [/knowlton/i, "knowlton2014"],
  [/azhar/i, "azhar2017"],
];

export function matchCitationFromText(text: string): CitationEntry | undefined {
  const hit = CITATION_TEXT_TO_ID.find(([pattern]) => pattern.test(text));
  return hit ? getCitation(hit[1]) : undefined;
}

/** Raw data-provenance sources (not academic papers, no DOIs) — `/legal`'s table. */
export type SourceEntry = { name: string; use: string };

export const SOURCES: SourceEntry[] = [
  { name: "Landsat 8/9 Collection 2 (USGS)", use: "Land surface temperature and NDVI composites" },
  { name: "WorldPop age-sex rasters", use: "Population density and elderly-share estimates" },
  { name: "ESA WorldCover v200", use: "Land cover, impervious surface, plantability screening" },
  { name: "Google Earth Engine", use: "Satellite data access and zonal statistics" },
  { name: "OpenStreetMap contributors", use: "Hospital locations (ODbL)" },
  { name: "Datameet Municipal Spatial Data", use: "BMC ward boundaries and slum-cluster polygons" },
  { name: "CARTO / OpenStreetMap", use: "Basemap tiles on the dashboard" },
];
