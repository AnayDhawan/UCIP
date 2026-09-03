/**
 * GET /api/v1/openapi.json
 *
 * OpenAPI 3.1 description of the public API. An API without a machine-readable
 * spec is a private API that happens to be reachable: nobody can generate a
 * client and nobody can tell what a response looks like without reading source.
 */

import { jsonResponse, optionsResponse } from "../_lib";

export const revalidate = 3600;

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  const origin = new URL(request.url).origin;

  const wardSchema = {
    type: "object",
    properties: {
      ward_id: { type: "string", example: "F/N", description: "BMC ward code." },
      hvi: {
        type: ["number", "null"],
        description: "Heat Vulnerability Index, 0-100. Higher is more vulnerable.",
      },
      rank: { type: ["integer", "null"], description: "1 is the most vulnerable of 24." },
      n_cells: { type: ["integer", "null"], description: "1 km grid cells in this ward." },
      contrib: {
        type: ["object", "null"],
        additionalProperties: { type: "number" },
        description:
          "Per-factor contribution to the score (weight x z-score). Sums to the pre-rescale index, so a ward's score decomposes exactly into its drivers.",
      },
    },
  };

  const recommendationSchema = {
    type: "object",
    properties: {
      ward_id: { type: "string" },
      intervention: { type: "string", example: "Cool roofs + reflective pavements" },
      rationale: { type: "string", description: "Why this rule fired for this ward." },
      citation: { type: "string", description: "The paper backing the intervention." },
      priority: { type: "integer", description: "1 is highest priority within the ward." },
      cell_count: { type: ["integer", "null"] },
    },
  };

  return jsonResponse({
    openapi: "3.1.0",
    info: {
      title: "UCIP API",
      version: "1.0.0",
      description:
        "Read-only access to Mumbai ward-level heat vulnerability data and cited nature-based cooling recommendations.\n\n" +
        "No authentication. Open CORS. Cached at the edge; the underlying data changes monthly at most.\n\n" +
        "Every response carries a `source` field of `database` or `snapshot`. The API falls back to committed static snapshots when the database is unavailable, so it stays up rather than returning 500s; snapshot data is at most one refresh behind.\n\n" +
        "Ward codes contain a slash for split wards and must be URL-encoded: `F/N` becomes `F%2FN`.",
      license: { name: "Apache-2.0", url: "https://github.com/AnayDhawan/UCIP/blob/main/LICENSE" },
    },
    servers: [{ url: `${origin}/api/v1` }],
    paths: {
      "/meta": {
        get: {
          summary: "What this deployment serves",
          description:
            "Coverage, counts, weighting method, licence and links. Includes whether the PCA weighting fell back to published literature weights.",
          responses: { "200": { description: "Deployment metadata" } },
        },
      },
      "/wards": {
        get: {
          summary: "All wards, ranked most vulnerable first",
          parameters: [
            { name: "limit", in: "query", schema: { type: "integer", minimum: 1, maximum: 24 } },
            {
              name: "geometry",
              in: "query",
              schema: { type: "boolean" },
              description: "Include ward polygons. Large; off by default.",
            },
          ],
          responses: {
            "200": {
              description: "Ward list",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      source: { type: "string", enum: ["database", "snapshot"] },
                      count: { type: "integer" },
                      wards: { type: "array", items: wardSchema },
                    },
                  },
                },
              },
            },
          },
        },
      },
      "/wards/{wardId}": {
        get: {
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
            "200": { description: "Ward and its ranked recommendations" },
            "400": { description: "Malformed ward code" },
            "404": { description: "No such ward" },
          },
        },
      },
      "/lookup": {
        get: {
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
            "200": { description: "The containing ward and its top recommendation" },
            "400": { description: "Missing or invalid coordinates" },
            "404": { description: "The point is outside every covered ward" },
          },
        },
      },
      "/recommendations": {
        get: {
          summary: "Nature-based-solution recommendations",
          parameters: [
            { name: "ward", in: "query", schema: { type: "string" }, example: "F%2FN" },
            { name: "limit", in: "query", schema: { type: "integer", maximum: 500 } },
          ],
          responses: {
            "200": {
              description: "Ranked recommendations",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      source: { type: "string" },
                      count: { type: "integer" },
                      recommendations: { type: "array", items: recommendationSchema },
                    },
                  },
                },
              },
            },
          },
        },
      },
      "/cells": {
        get: {
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
              description: "minLon,minLat,maxLon,maxLat. Returns cells overlapping the box.",
            },
            { name: "limit", in: "query", schema: { type: "integer", maximum: 1000 } },
            { name: "geometry", in: "query", schema: { type: "boolean" } },
          ],
          responses: { "200": { description: "Grid cells" }, "400": { description: "Bad bbox" } },
        },
      },
    },
    components: {
      schemas: { Ward: wardSchema, Recommendation: recommendationSchema },
    },
  });
}
