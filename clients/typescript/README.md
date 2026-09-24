# ucip-client

Typed TypeScript client for the [UCIP API](https://uciplatform.vercel.app/api/v1/openapi.json):
Mumbai ward-level heat vulnerability data and cited nature-based cooling
recommendations.

No authentication, no key, no account. The API is public and read-only.

```bash
npm install ucip-client
```

## Three lines

```ts
import { UcipClient } from "ucip-client";

const wards = await new UcipClient().allWards();
console.log(wards[0]); // { ward_id: "C", hvi: 73.56, rank: 1, ... }
```

## What you can ask it

```ts
const ucip = new UcipClient();

await ucip.meta();                          // coverage, counts, data vintage
await ucip.wards({ limit: 5 });             // ranked most vulnerable first
await ucip.ward("F/N");                     // one ward + its recommendations
await ucip.lookup(19.076, 72.877);          // which ward contains this point
await ucip.recommendations({ ward: "C" });  // cited interventions
await ucip.cells({ bbox: "72.80,19.00,72.95,19.15" });
await ucip.export("wards");                 // the whole dataset, one request
await ucip.exportCsv("cells");              // the same as CSV text
```

`allWards()` and `allCells()` unwrap the response envelope when you want the
records rather than the metadata around them.

## Bulk access

Use `export()`. It is one edge-cached request for the complete dataset, rather
than paging the other endpoints:

```ts
const fc = await ucip.export("cells");   // GeoJSON FeatureCollection, 541 cells
```

This project runs on a free-tier database. Paging in a loop is both slower for
you and the thing most likely to meet the rate limiter.

## Reading the data honestly

Three fields exist because the numbers deserve caveats, and a client that hides
them is doing you a disservice:

- **`source`** on every response is `"database"` or `"snapshot"`. `snapshot`
  means the database was unreachable and committed static files were served
  instead, at most one refresh behind. Field names and the key set are
  identical either way, so you never need to branch on it; it is there for when
  you are debugging or when data vintage matters.
- **`single_factor_dominated`** on a ward marks a score driven by one indicator
  rather than a real combination of seven. On the current dataset no ward is
  flagged, but do not assume that for a future refresh or another city.
- **`composite_window`** from `meta()` is the Landsat window the measurements
  come from. It is older than `generated_at`, and it is the one that says how
  old the underlying observations actually are.

Methodology and limitations: <https://uciplatform.vercel.app/methodology>.

## Errors

```ts
import { UcipHttpError, UcipNetworkError, UcipError } from "ucip-client";

try {
  await ucip.ward("ZZ");
} catch (err) {
  if (err instanceof UcipHttpError) {
    err.status;             // 404
    err.detail;             // the API's own message
    err.hint;               // its suggested next step, when there is one
    err.isRateLimited;      // true only on 429
    err.retryAfterSeconds;  // from the retry-after header
  } else if (err instanceof UcipNetworkError) {
    // never reached the API: DNS, TLS, connection refused, timeout
  }
}
```

Everything thrown extends `UcipError`, so one `instanceof` catches all of it.

The client does **not** retry. The failure you are most likely to hit is a 429
from defeating the edge cache in a loop, and retrying that makes it worse.
`retryAfterSeconds` is there for backing off deliberately.

## Options

```ts
new UcipClient({
  baseUrl: "http://localhost:3000/api/v1",  // defaults to the public deployment
  timeoutMs: 10_000,                        // no client-side timeout by default
  headers: { "user-agent": "my-tool/1.0" }, // be identifiable
  fetch: myFetch,                           // defaults to the global fetch
});
```

Every method takes an optional `AbortSignal` as its last argument.

Node 18 or newer, or any modern browser. No dependencies.

## Where the types come from

`src/types.gen.ts` is generated from the OpenAPI spec at
`frontend/src/lib/openapiSpec.ts`, which is the same module the API serves its
spec from. CI regenerates and diffs, and the UCIP frontend typechecks its own
route handlers against these types, so an API change that is not reflected here
fails the build rather than shipping a client that quietly describes the wrong
shapes.

Do not edit `types.gen.ts`. Change the spec and run `npm run generate`.

## Development

```bash
npm install
npm run generate     # rebuild types.gen.ts from the spec
npm test             # stubbed fetch, no network
UCIP_LIVE=1 npm test # also runs the live checks against the deployment
npm run build
```

## Licence

Apache-2.0. The data has its own per-source terms: see
<https://uciplatform.vercel.app/legal>.
