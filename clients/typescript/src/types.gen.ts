/**
 * Response types for the UCIP API.
 *
 * GENERATED FILE. Do not edit.
 *
 * Produced by scripts/generate.ts from the OpenAPI spec in
 * frontend/src/lib/openapiSpec.ts. Regenerate with `npm run generate`.
 * CI regenerates and diffs, so an API change that is not reflected here
 * fails the build rather than shipping a client that describes the wrong
 * shapes.
 */

export type Ward = {
  /** BMC ward code. */
  ward_id: string;
  /** Heat Vulnerability Index, 0-100. Higher is more vulnerable. */
  hvi?: number | null;
  /** 1 is the most vulnerable of 24. */
  rank?: number | null;
  /** 1 km grid cells in this ward. */
  n_cells?: number | null;
  /**
   * Per-factor contribution to the score (weight x z-score). Sums to the
   * pre-rescale index, so a ward's score decomposes exactly into its
   * drivers.
   */
  contrib?: Record<string, number> | null;
  /**
   * The indicator with the largest absolute contribution to this ward's
   * score.
   */
  dominant_factor?: string | null;
  /**
   * That indicator's share of total absolute contribution, 0 to 1. An even
   * spread across the eight indicators is 0.125.
   */
  dominant_share?: number | null;
  /**
   * True when one indicator accounts for half or more of the movement in the
   * score, so the ranking is effectively driven by that one measure.
   */
  single_factor_dominated?: boolean | null;
  /** GeoJSON geometry. Only present when `geometry=true` was requested. */
  geom_geojson?: {
    type?: string;
    coordinates?: unknown[];
  } | null;
};

export type Recommendation = {
  /**
   * Omitted on /wards/{wardId}, where the ward is already the subject of the
   * response.
   */
  ward_id?: string;
  intervention: string;
  /** Why this rule fired for this ward. */
  rationale: string;
  /** The paper backing the intervention. */
  citation: string;
  /** 1 is highest priority within the ward. */
  priority: number;
  /** How many grid cells in the ward triggered this rule. */
  cell_count?: number | null;
};

/**
 * One 1 km analysis cell. These are the measurements the ward scores are
 * built from, published so the rollup can be checked rather than trusted.
 */

export type Cell = {
  grid_id: string | number;
  ward_id: string;
  /** Dry-season land surface temperature, Celsius. */
  lst_c?: number | null;
  /** Normalised difference vegetation index, -1 to 1. */
  ndvi?: number | null;
  /** NDVI in the previous comparison window. */
  ndvi_prev?: number | null;
  pop_density_km2?: number | null;
  /** Share of population aged 60 or over. */
  elderly_pct?: number | null;
  slum_pct?: number | null;
  /** Distance to the nearest hospital, metres. */
  hospital_dist_m?: number | null;
  impervious_pct?: number | null;
  hvi?: number | null;
  /**
   * Whether the ecological filter allows tree planting here. False on native
   * open habitat, water, wetland, mangrove and heavily sealed cells.
   */
  plantable?: boolean | null;
  /** ESA WorldCover class code. */
  worldcover_class?: number | null;
  /** GeoJSON geometry. Only present when `geometry=true` was requested. */
  geom_geojson?: {
    type?: string;
    coordinates?: unknown[];
  } | null;
};

export type Meta = {
  name?: string;
  api_version?: string;
  description?: string;
  coverage?: {
    cities?: Array<{
      name?: string;
      wards?: number | null;
    }>;
    note?: string;
  };
  counts?: {
    wards?: number | null;
    recommendations?: number | null;
    citations?: number | null;
  };
  /**
   * When the pipeline last produced this data. Null until a refresh run has
   * committed a run log; a guessed date would defeat the point of the field.
   */
  generated_at?: string | null;
  /**
   * The Landsat dry-season window the figures were computed from. This is
   * older than generated_at and is the one that says how old the
   * measurements actually are.
   */
  composite_window?: {
    start?: string;
    end?: string;
  } | null;
  method?: {
    index?: string;
    /**
     * Says explicitly when the PCA weighting fell back to published
     * literature weights, because that changes how the scores were derived.
     */
    weighting?: string;
    explainability?: string;
    limitations_url?: string;
  };
  database_configured?: boolean;
  license?: {
    code?: string;
    data?: string;
  };
  links?: {
    documentation?: string;
    methodology?: string;
    repository?: string;
  };
};

export type ApiError = {
  error: {
    status: number;
    message: string;
    /** Present when there is a useful next step. */
    hint?: string;
  };
};

export type WardListResponse = {
  /**
   * Which backend answered. `snapshot` means the database was unavailable
   * and the committed static files were served instead, at most one refresh
   * behind.
   */
  source: "database" | "snapshot";
  count: number;
  wards: Ward[];
};

export type WardDetailResponse = {
  /**
   * Which backend answered. `snapshot` means the database was unavailable
   * and the committed static files were served instead, at most one refresh
   * behind.
   */
  source: "database" | "snapshot";
  ward: Ward;
  recommendations: Recommendation[];
};

export type LookupResponse = {
  /**
   * Which backend answered. `snapshot` means the database was unavailable
   * and the committed static files were served instead, at most one refresh
   * behind.
   */
  source: "database" | "snapshot";
  /** The coordinate as parsed, echoed back. */
  query: {
    lat?: number;
    lon?: number;
  };
  ward: Ward;
  /** The highest-priority recommendation for the containing ward, if any. */
  top_recommendation?: Recommendation | null;
};

export type RecommendationListResponse = {
  /**
   * Which backend answered. `snapshot` means the database was unavailable
   * and the committed static files were served instead, at most one refresh
   * behind.
   */
  source: "database" | "snapshot";
  count: number;
  recommendations: Recommendation[];
};

export type CellListResponse = {
  /**
   * Which backend answered. `snapshot` means the database was unavailable
   * and the committed static files were served instead, at most one refresh
   * behind.
   */
  source: "database" | "snapshot";
  count: number;
  cells: Cell[];
};

/** Query parameters for `GET /wards`. */
export type ListWardsParams = {
  limit?: number;
  /** Include ward polygons. Large; off by default. */
  geometry?: boolean;
};

/** Query parameters for `GET /lookup`. */
export type LookupPointParams = {
  lat?: number;
  lon?: number;
};

/** Query parameters for `GET /recommendations`. */
export type ListRecommendationsParams = {
  ward?: string;
  limit?: number;
};

/** Query parameters for `GET /cells`. */
export type ListCellsParams = {
  ward?: string;
  /**
   * minLon,minLat,maxLon,maxLat. Returns cells overlapping the box. A bbox
   * query is served from the snapshot, which is the source that carries
   * geometry.
   */
  bbox?: string;
  limit?: number;
  geometry?: boolean;
};

/** Query parameters for `GET /export`. */
export type ExportDatasetParams = {
  dataset?: "cells" | "wards";
  format?: "geojson" | "csv";
};
