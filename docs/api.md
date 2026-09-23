# UCIP API

Read-only HTTP access to Mumbai ward-level heat vulnerability data and the cited
nature-based cooling recommendations derived from it.

**Base URL:** `https://uciplatform.vercel.app/api/v1`
**Spec:** [`/api/v1/openapi.json`](https://uciplatform.vercel.app/api/v1/openapi.json) (OpenAPI 3.1)

No authentication, no key, no rate limit today. Open CORS, so browser code can
call it directly. Everything served here is already public: the same numbers sit
in the committed GeoJSON snapshots in this repository and on the dashboard.

Want all of it? Use [`/export`](#get-exportdatasetformat), one request for the
whole dataset as GeoJSON or CSV. What `v1` guarantees, and what would require a
`v2`, is written down under [Versioning](#versioning).

## Two things to know before you start

**Ward codes contain slashes.** Mumbai's BMC wards include split wards like
`F/N`, `G/S` and `R/C`. In a path segment they must be URL-encoded:

```
/api/v1/wards/F%2FN
```

**Every response says where it came from.** Each carries a `source` field of
`database` or `snapshot`. The API reads Supabase when it is available and falls
back to the committed static snapshots when it is not, rather than returning a
500. Snapshot data is at most one refresh behind. This is the same demo-safe
principle the dashboard was built on, and it is why the site survived the
Supabase project being deleted in September 2026.

## Endpoints

### `GET /meta`

What this deployment is serving: coverage, row counts, the weighting method
actually used (PCA, or the published-literature fallback if the PCA was
rejected), licence terms and links. It also reports `generated_at` (when the
pipeline last refreshed the data) and `composite_window` (the dry-season Landsat
window the figures were computed from); both are null until a refresh run has
committed its run log.

### `GET /wards`

All 24 wards, ranked most vulnerable first.

| Param | Type | Default | Notes |
|---|---|---|---|
| `limit` | 1-24 | 24 | |
| `geometry` | boolean | false | Include ward polygons. Roughly 1 MB; off by default. |

```bash
curl 'https://uciplatform.vercel.app/api/v1/wards?limit=3'
```

Each ward carries `contrib`, the per-factor contribution to its score (weight
times z-score). This is the explainability layer: the index is a transparent
linear combination, so a ward's score decomposes exactly into its drivers. There
is no post-hoc attribution because there is no black box.

### `GET /wards/{wardId}`

One ward with its ranked recommendations, each carrying the rationale that fired
the rule and the paper backing it.

```bash
curl 'https://uciplatform.vercel.app/api/v1/wards/F%2FN'
```

`400` for a malformed code, `404` for a well-formed code that does not exist.

### `GET /lookup?lat=&lon=`

The ward containing a coordinate, with its top recommendation. This is the
endpoint for "what is the heat risk where I am", without needing to know a ward
code first.

```bash
curl 'https://uciplatform.vercel.app/api/v1/lookup?lat=19.076&lon=72.877'
```

`404` when the point falls outside all 24 wards, which currently means anywhere
outside Mumbai.

### `GET /recommendations?ward=&limit=`

Recommendations across all wards, or one ward, ordered by priority.

### `GET /cells?ward=&bbox=&limit=&geometry=`

The 1 km analysis grid: the per-cell measurements the ward scores are built
from. Use this to check the working rather than trusting the ward rollup.

`bbox` is `minLon,minLat,maxLon,maxLat` and returns cells overlapping the box.

```bash
curl 'https://uciplatform.vercel.app/api/v1/cells?bbox=72.80,19.00,72.95,19.15'
```

### `GET /export?dataset=&format=`

The whole dataset in one cached call. **This is the preferred route for bulk
access**, rather than paging the endpoints above.

| Parameter | Values | Default |
|---|---|---|
| `dataset` | `cells` (541 grid cells), `wards` (24 BMC wards) | `cells` |
| `format` | `geojson`, `csv` | `geojson` |

```
/api/v1/export?dataset=cells&format=csv
```

CSV rows lead with the identifier and the feature centre as plain `lon` and
`lat` columns, so the data plots in pandas or R without a geometry library. For
cells that centre is exact to well under a metre, since the cells are squares;
for wards it is a rough label point, not a centroid.

Served from the published snapshots rather than the database, on purpose. A bulk
export is by definition the complete published dataset, which is exactly what
the snapshots are, and routing the heaviest response in the API around the
free-tier database keeps it available for everything else.

Column meanings, units, valid ranges and known limitations are in
[`DATA-DICTIONARY.md`](DATA-DICTIONARY.md).

## Caching

Responses are edge-cached for an hour with a day of stale-while-revalidate. The
underlying data changes monthly at most (see
[`pipeline/README.md`](../pipeline/README.md) on refresh cadence), so this keeps
the free-tier database out of the request path for nearly all traffic.

Please do not poll. If you want the whole dataset, use
[`/export`](#get-exportdatasetformat), which is one request instead of many.

## Versioning

`v1` is in the path, and this is what it promises.

**These can change without a new version.** Build against the API expecting
them:

- New endpoints.
- New fields on an existing response. Read by name and ignore what you do not
  recognise.
- New values in a `dataset`, `format` or similar parameter.
- Data values changing on a refresh. The numbers are recomputed monthly at
  most; a ward's score moving is the API working, not breaking. Every response
  carries the refresh date via [`/meta`](#get-meta).
- Cache durations, error message wording, and the order of items in a list
  where no order is documented.

**These need `v2`.** They will not happen inside `v1`:

- Removing or renaming a field.
- Changing a field's type, or its units. `hospital_dist_m` will not quietly
  become kilometres.
- Changing what a field means while keeping its name.
- Removing an endpoint or a parameter, or making an optional parameter
  required.
- Changing the shape of an error response.

**Deprecation.** If `v2` arrives, `v1` keeps serving for at least six months
from the day `v2` ships, and during that window `v1` responses carry a
`Deprecation` header with the removal date. A version is never withdrawn
without that notice.

**Where changes are announced.** In the changelog below, in
[`CHANGELOG.md`](../CHANGELOG.md), and in the GitHub release notes for the
version that carries them.

### API changelog

Changes to this API, newest first. Data refreshes are not listed here; they are
visible through [`/meta`](#get-meta).

| Date | Change |
|---|---|
| 2026-09-23 | Added [`/export`](#get-exportdatasetformat) for bulk access as GeoJSON or CSV. Additive, no existing response changed. |
| 2026-09-23 | Documented this versioning policy. No behaviour change. |
| 2026-09-18 | `v1` published with `/meta`, `/wards`, `/wards/{wardId}`, `/lookup`, `/recommendations`, `/cells` and `/openapi.json`. |

## Limits and honesty

- **Mumbai only.** The pipeline is city-agnostic but no second city is
  configured yet.
- **A point in time.** Scores come from a single dry-season composite, not a
  trend. Multi-year time series is tracked in issue #64.
- **Proxies are proxies.** `elderly_pct` is a modelled WorldPop surface, not a
  census count, and `hospital_dist_m` is straight-line rather than travel
  distance. Both are documented on the [methodology page](https://uciplatform.vercel.app/methodology).
- **Not validated against ground stations yet.** Land surface temperature is
  satellite-derived and is not air temperature. Issue #65 tracks correlating it
  against weather-station observations.
- **`v1` is young.** The stability promise is real and written down under
  [Versioning](#versioning), but it has not been tested by a second version yet.

## Licence

Code is Apache 2.0. The data carries the terms of its sources (Landsat, WorldPop,
ESA WorldCover, OpenStreetMap, Datameet); see
[`/legal`](https://uciplatform.vercel.app/legal). If you use this in published
work, cite the repository.
