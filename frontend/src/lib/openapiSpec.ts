/**
 * The OpenAPI 3.1 description of the public v1 API, as plain data.
 *
 * This lives in its own module, with no imports, for one reason: the client
 * generators read it. `clients/typescript/scripts/generate.ts` imports
 * `buildSpec` directly and emits types from it, which means the published
 * clients and the served spec cannot disagree, because there is only one of
 * them. Were this still inline in the route handler, a generator would have to
 * either scrape a running deployment or keep its own copy of the shapes, and a
 * second copy is how a client starts lying about the API.
 *
 * Response schemas are complete here, not sketched. An earlier version
 * described parameters properly but left most responses as a bare
 * `description` string, which is enough for a human reading the docs and
 * useless to a generator: every response type would come out as `unknown`.
 */

/** Loosely typed on purpose: this is a JSON document, not a modelled object. */
type Schema = Record<string, unknown>;

const nullableNumber = { type: ["number", "null"] };
const nullableInteger = { type: ["integer", "null"] };

/** Where a response came from. Present on every data response. */
const sourceField = {
  type: "string",
  enum: ["database", "snapshot"],
  description:
    "Which backend answered. `snapshot` means the database was unavailable and " +
    "the committed static files were served instead, at most one refresh behind.",
};

const geometry: Schema = {
  type: ["object", "null"],
  description: "GeoJSON geometry. Only present when `geometry=true` was requested.",
  properties: {
    type: { type: "string", example: "MultiPolygon" },
    coordinates: { type: "array", items: {} },
  },
};

const ward: Schema = {
  type: "object",
  required: ["ward_id"],
  properties: {
    ward_id: { type: "string", example: "F/N", description: "BMC ward code." },
    hvi: {
      ...nullableNumber,
      description: "Heat Vulnerability Index, 0-100. Higher is more vulnerable.",
    },
    rank: { ...nullableInteger, description: "1 is the most vulnerable of 24." },
    n_cells: { ...nullableInteger, description: "1 km grid cells in this ward." },
    contrib: {
      type: ["object", "null"],
      additionalProperties: { type: "number" },
      description:
        "Per-factor contribution to the score (weight x z-score). Sums to the " +
        "pre-rescale index, so a ward's score decomposes exactly into its drivers.",
    },
    dominant_factor: {
      type: ["string", "null"],
      description: "The indicator with the largest absolute contribution to this ward's score.",
    },
    dominant_share: {
      ...nullableNumber,
      description:
        "That indicator's share of total absolute contribution, 0 to 1. " +
        "An even spread across the eight indicators is 0.125.",
    },
    single_factor_dominated: {
      type: ["boolean", "null"],
      description:
        "True when one indicator accounts for half or more of the movement in " +
        "the score, so the ranking is effectively driven by that one measure.",
    },
    geom_geojson: geometry,
  },
};

const recommendation: Schema = {
  type: "object",
  required: ["intervention", "rationale", "citation", "priority"],
  properties: {
    ward_id: {
      type: "string",
      description:
        "Omitted on /wards/{wardId}, where the ward is already the subject of the response.",
    },
    intervention: { type: "string", example: "Cool roofs + reflective pavements" },
    rationale: { type: "string", description: "Why this rule fired for this ward." },
    citation: { type: "string", description: "The paper backing the intervention." },
    priority: { type: "integer", description: "1 is highest priority within the ward." },
    cell_count: {
      ...nullableInteger,
      description: "How many grid cells in the ward triggered this rule.",
    },
  },
};

const cell: Schema = {
  type: "object",
  required: ["grid_id", "ward_id"],
  description:
    "One 1 km analysis cell. These are the measurements the ward scores are " +
    "built from, published so the rollup can be checked rather than trusted.",
  properties: {
    grid_id: { type: ["string", "integer"], example: "cell_0000" },
    ward_id: { type: "string" },
    lst_c: { ...nullableNumber, description: "Dry-season land surface temperature, Celsius." },
    ndvi: { ...nullableNumber, description: "Normalised difference vegetation index, -1 to 1." },
    ndvi_prev: { ...nullableNumber, description: "NDVI in the previous comparison window." },
    pop_density_km2: nullableNumber,
    elderly_pct: { ...nullableNumber, description: "Share of population aged 60 or over." },
    slum_pct: nullableNumber,
    hospital_dist_m: { ...nullableNumber, description: "Distance to the nearest hospital, metres." },
    impervious_pct: nullableNumber,
    hvi: nullableNumber,
    plantable: {
      type: ["boolean", "null"],
      description:
        "Whether the ecological filter allows tree planting here. False on native " +
        "open habitat, water, wetland, mangrove and heavily sealed cells.",
    },
    worldcover_class: { ...nullableInteger, description: "ESA WorldCover class code." },
    geom_geojson: geometry,
  },
};

const meta: Schema = {
  type: "object",
  properties: {
    name: { type: "string" },
    api_version: { type: "string", example: "v1" },
    description: { type: "string" },
    coverage: {
      type: "object",
      properties: {
        cities: {
          type: "array",
          items: {
            type: "object",
            properties: { name: { type: "string" }, wards: nullableInteger },
          },
        },
        note: { type: "string" },
      },
    },
    counts: {
      type: "object",
      properties: {
        wards: nullableInteger,
        recommendations: nullableInteger,
        citations: nullableInteger,
      },
    },
    generated_at: {
      type: ["string", "null"],
      format: "date-time",
      description:
        "When the pipeline last produced this data. Null until a refresh run has " +
        "committed a run log; a guessed date would defeat the point of the field.",
    },
    composite_window: {
      type: ["object", "null"],
      description:
        "The Landsat dry-season window the figures were computed from. This is " +
        "older than generated_at and is the one that says how old the " +
        "measurements actually are.",
      properties: {
        start: { type: "string", format: "date" },
        end: { type: "string", format: "date" },
      },
    },
    method: {
      type: "object",
      properties: {
        index: { type: "string" },
        weighting: {
          type: "string",
          description:
            "Says explicitly when the PCA weighting fell back to published " +
            "literature weights, because that changes how the scores were derived.",
        },
        explainability: { type: "string" },
        limitations_url: { type: "string" },
      },
    },
    database_configured: { type: "boolean" },
    license: {
      type: "object",
      properties: { code: { type: "string" }, data: { type: "string" } },
    },
    links: {
      type: "object",
      properties: {
        documentation: { type: "string" },
        methodology: { type: "string" },
        repository: { type: "string" },
      },
    },
  },
};

const errorSchema: Schema = {
  type: "object",
  required: ["error"],
  properties: {
    error: {
      type: "object",
      required: ["status", "message"],
      properties: {
        status: { type: "integer" },
        message: { type: "string" },
        hint: { type: "string", description: "Present when there is a useful next step." },
      },
    },
  },
};

/** `$ref` to a component schema, spelled once. */
const ref = (name: string) => ({ $ref: `#/components/schemas/${name}` });

/** A JSON response body of the given component schema. */
const jsonBody = (description: string, schema: Schema | { $ref: string }) => ({
  description,
  content: { "application/json": { schema } },
});

const errorResponse = (description: string) => jsonBody(description, ref("Error"));

/** The 429 every endpoint can return, spelled once. */
const rateLimitedResponse = errorResponse(
  "Rate limited. The whole dataset is one call to /export; cache it rather than polling."
);

export function buildSpec(origin: string) {
  return {
    openapi: "3.1.0",
    info: {
      title: "UCIP API",
      version: "1.0.0",
      description:
        "Read-only access to Mumbai ward-level heat vulnerability data and cited nature-based cooling recommendations.\n\n" +
        "No authentication. Open CORS. Cached at the edge; the underlying data changes monthly at most.\n\n" +
        "Every response carries a `source` field of `database` or `snapshot`. The API falls back to committed static snapshots when the database is unavailable, so it stays up rather than returning 500s; snapshot data is at most one refresh behind. Both sources return identical field names and an identical key set, so a client never needs to branch on `source`.\n\n" +
        "Ward codes contain a slash for split wards and must be URL-encoded: `F/N` becomes `F%2FN`.",
      license: { name: "Apache-2.0", url: "https://github.com/AnayDhawan/UCIP/blob/main/LICENSE" },
    },
    servers: [{ url: `${origin}/api/v1` }],
    paths: {
      "/meta": {
        get: {
          operationId: "getMeta",
          summary: "What this deployment serves",
          description:
            "Coverage, counts, weighting method, licence and links. Includes whether the PCA weighting fell back to published literature weights, and the composite window the figures were computed from.",
          responses: {
            "200": jsonBody("Deployment metadata", ref("Meta")),
            "429": rateLimitedResponse,
          },
        },
      },
      "/wards": {
        get: {
          operationId: "listWards",
          summary: "All wards, ranked most vulnerable first",
          parameters: [
            {
              name: "limit",
              in: "query",
              schema: { type: "integer", minimum: 1, maximum: 24, default: 24 },
            },
            {
              name: "geometry",
              in: "query",
              schema: { type: "boolean", default: false },
              description: "Include ward polygons. Large; off by default.",
            },
          ],
          responses: {
            "200": jsonBody("Ward list", ref("WardListResponse")),
            "429": rateLimitedResponse,
            "503": errorResponse("Ward data is temporarily unavailable."),
          },
        },
      },
      "/wards/{wardId}": {
        get: {
          operationId: "getWard",
          summary: "One ward with its recommendations",
          parameters: [
            {
              name: "wardId",
              in: "path",
              required: true,
              schema: { type: "string" },
              example: "F%2FN",
              description: "BMC ward code, URL-encoded.",
            },
          ],
          responses: {
            "200": jsonBody("Ward and its ranked recommendations", ref("WardDetailResponse")),
            "400": errorResponse("Malformed ward code"),
            "404": errorResponse("No such ward"),
            "429": rateLimitedResponse,
          },
        },
      },
      "/lookup": {
        get: {
          operationId: "lookupPoint",
          summary: "Find the ward containing a coordinate",
          description:
            "Point-in-polygon lookup. Answers 'what is the heat risk where I am' without needing to know a ward code.",
          parameters: [
            {
              name: "lat",
              in: "query",
              required: true,
              schema: { type: "number", minimum: -90, maximum: 90 },
              example: 19.076,
            },
            {
              name: "lon",
              in: "query",
              required: true,
              schema: { type: "number", minimum: -180, maximum: 180 },
              example: 72.877,
            },
          ],
          responses: {
            "200": jsonBody("The containing ward and its top recommendation", ref("LookupResponse")),
            "400": errorResponse("Missing or invalid coordinates"),
            "404": errorResponse("The point is outside every covered ward"),
            "429": rateLimitedResponse,
          },
        },
      },
      "/recommendations": {
        get: {
          operationId: "listRecommendations",
          summary: "Nature-based-solution recommendations",
          parameters: [
            { name: "ward", in: "query", schema: { type: "string" }, example: "F%2FN" },
            { name: "limit", in: "query", schema: { type: "integer", maximum: 500 } },
          ],
          responses: {
            "200": jsonBody("Ranked recommendations", ref("RecommendationListResponse")),
            "400": errorResponse("Invalid ward code"),
            "429": rateLimitedResponse,
          },
        },
      },
      "/cells": {
        get: {
          operationId: "listCells",
          summary: "The 1 km analysis grid",
          description:
            "Per-cell measurements the ward scores are built from, for checking the working rather than trusting the rollup.",
          parameters: [
            { name: "ward", in: "query", schema: { type: "string" } },
            {
              name: "bbox",
              in: "query",
              schema: { type: "string" },
              example: "72.80,19.00,72.95,19.15",
              description:
                "minLon,minLat,maxLon,maxLat. Returns cells overlapping the box. " +
                "A bbox query is served from the snapshot, which is the source that carries geometry.",
            },
            { name: "limit", in: "query", schema: { type: "integer", maximum: 1000, default: 541 } },
            { name: "geometry", in: "query", schema: { type: "boolean", default: false } },
          ],
          responses: {
            "200": jsonBody("Grid cells", ref("CellListResponse")),
            "400": errorResponse("Bad bbox or ward code"),
            "429": rateLimitedResponse,
            "503": errorResponse("Cell data is temporarily unavailable."),
          },
        },
      },
      "/export": {
        get: {
          operationId: "exportDataset",
          summary: "The whole dataset in one call",
          description:
            "The complete published dataset as GeoJSON or CSV. The preferred route for bulk access: one cached request instead of paging the other endpoints. CSV rows carry the feature centre as lon/lat columns, so no geometry library is needed.",
          parameters: [
            {
              name: "dataset",
              in: "query",
              schema: { type: "string", enum: ["cells", "wards"], default: "cells" },
            },
            {
              name: "format",
              in: "query",
              schema: { type: "string", enum: ["geojson", "csv"], default: "geojson" },
            },
          ],
          responses: {
            "200": {
              description: "The full dataset",
              content: {
                "application/geo+json": {
                  schema: {
                    type: "object",
                    description: "A GeoJSON FeatureCollection.",
                    properties: {
                      type: { type: "string", enum: ["FeatureCollection"] },
                      features: { type: "array", items: { type: "object" } },
                    },
                  },
                },
                "text/csv": { schema: { type: "string" } },
              },
            },
            "400": errorResponse("Unknown dataset or format"),
            "429": rateLimitedResponse,
          },
        },
      },
    },
    components: {
      schemas: {
        Ward: ward,
        Recommendation: recommendation,
        Cell: cell,
        Meta: meta,
        Error: errorSchema,
        WardListResponse: {
          type: "object",
          required: ["source", "count", "wards"],
          properties: {
            source: sourceField,
            count: { type: "integer" },
            wards: { type: "array", items: ref("Ward") },
          },
        },
        WardDetailResponse: {
          type: "object",
          required: ["source", "ward", "recommendations"],
          properties: {
            source: sourceField,
            ward: ref("Ward"),
            recommendations: { type: "array", items: ref("Recommendation") },
          },
        },
        LookupResponse: {
          type: "object",
          required: ["source", "query", "ward"],
          properties: {
            source: sourceField,
            query: {
              type: "object",
              description: "The coordinate as parsed, echoed back.",
              properties: { lat: { type: "number" }, lon: { type: "number" } },
            },
            ward: ref("Ward"),
            top_recommendation: {
              oneOf: [ref("Recommendation"), { type: "null" }],
              description: "The highest-priority recommendation for the containing ward, if any.",
            },
          },
        },
        RecommendationListResponse: {
          type: "object",
          required: ["source", "count", "recommendations"],
          properties: {
            source: sourceField,
            count: { type: "integer" },
            recommendations: { type: "array", items: ref("Recommendation") },
          },
        },
        CellListResponse: {
          type: "object",
          required: ["source", "count", "cells"],
          properties: {
            source: sourceField,
            count: { type: "integer" },
            cells: { type: "array", items: ref("Cell") },
          },
        },
      },
    },
  };
}
