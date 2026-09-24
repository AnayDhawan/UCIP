/**
 * GET /api/v1/openapi.json
 *
 * OpenAPI 3.1 description of the public API. An API without a machine-readable
 * spec is a private API that happens to be reachable: nobody can generate a
 * client and nobody can tell what a response looks like without reading source.
 *
 * The document itself is built in `@/lib/openapiSpec`, which has no imports so
 * that the client generators can read it directly rather than scraping a
 * running deployment. This route is the HTTP wrapper around it.
 */

import { buildSpec } from "@/lib/openapiSpec";
import { jsonResponse, optionsResponse } from "../_lib";

export const revalidate = 3600;

export function OPTIONS() {
  return optionsResponse();
}

export async function GET(request: Request) {
  return jsonResponse(buildSpec(new URL(request.url).origin));
}
