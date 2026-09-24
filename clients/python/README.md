# ucip

Python client for the [UCIP API](https://uciplatform.vercel.app): Mumbai
ward-level heat vulnerability data and cited nature-based cooling
recommendations, as pandas and geopandas frames.

No authentication, no key, no account. The API is public and read-only.

```bash
pip install ucip
```

## Three lines

```python
import ucip

wards = ucip.Ucip().wards_geo()
wards.plot(column="hvi", legend=True)
```

A `GeoDataFrame` of all 24 wards in EPSG:4326, indexed by ward code and sorted
by rank, with the per-factor contributions flattened into `contrib_*` columns.

## Frames

```python
from ucip import Ucip

api = Ucip()

api.wards_frame()             # 24 wards, indexed by ward code, ranked
api.cells_frame()             # the 541-cell analysis grid, indexed by cell id
api.recommendations_frame()   # every intervention, with its citation
api.wards_geo()               # wards with geometry
api.cells_geo()               # the grid with geometry
```

`wards_geo()` and `cells_geo()` are one cached request for the whole dataset,
not a paging loop. This project runs on a free-tier database; paging the
per-record endpoints to build a frame is slower for you and is the surest way
to meet the rate limiter.

## Raw responses

When you want exactly what the API sent, as typed dicts:

```python
api.meta()                                # coverage, counts, data vintage
api.wards(limit=5)
api.ward("F/N")                           # the slash is encoded for you
api.lookup(19.076, 72.877)                # which ward contains this point
api.recommendations(ward="C")
api.cells(bbox="72.80,19.00,72.95,19.15")
api.export("wards")                       # GeoJSON FeatureCollection
api.export_csv("cells")                   # CSV text, with lon/lat columns
```

## Reading the data honestly

Three fields exist because the numbers deserve caveats, and a client that hides
them is doing you a disservice.

**`single_factor_dominated`**, on each ward, marks a score driven by one
indicator rather than a real combination of seven. Check it before treating a
rank as a composite:

```python
wards = api.wards_frame()
wards[wards["single_factor_dominated"]]     # empty on the current dataset
```

It is empty today. Do not assume that for a future refresh or another city.

**`source`**, on every raw response, is `"database"` or `"snapshot"`.
`snapshot` means the database was unreachable and committed static files were
served instead, at most one refresh behind. Field names and the key set are
identical either way, so you never need to branch on it; it is there for when
data vintage matters.

**`composite_window`**, from `meta()`, is the Landsat window the measurements
come from. It is older than `generated_at`, and it is the one that says how old
the underlying observations actually are.

```python
meta = api.meta()
meta["generated_at"]        # when the pipeline last ran
meta["composite_window"]    # what the imagery actually covers
```

Every recommendation carries the paper it rests on, and
`recommendations_frame()` keeps that column. A planting recommendation
separated from its citation is the artefact this project exists not to produce.

Methodology and limitations: <https://uciplatform.vercel.app/methodology>.

## Errors

```python
from ucip import UcipHTTPError, UcipNetworkError, UcipError

try:
    api.ward("ZZ")
except UcipHTTPError as err:
    err.status           # 404
    err.detail           # the API's own message
    err.hint             # its suggested next step, when there is one
    err.is_rate_limited  # True only on 429
    err.retry_after      # seconds, from the retry-after header
except UcipNetworkError:
    ...                  # never reached the API
```

Everything raised inherits from `UcipError`.

The client does **not** retry. The failure you are most likely to hit is a 429
from defeating the edge cache in a loop, and retrying makes that worse.
`retry_after` is there for backing off deliberately.

## Options

```python
Ucip(
    "http://localhost:3000/api/v1",   # defaults to the public deployment
    timeout=30.0,
    user_agent="my-analysis/1.0",     # be identifiable
    session=my_requests_session,
)
```

Python 3.10 or newer. Depends on `requests`, `pandas` and `geopandas`, all
imported lazily so `import ucip` does not pay for GDAL bindings.

## Citing this

The dataset has a DOI. If it appears in something you publish, cite it:

> Dhawan, A. UCIP: Urban Climate Intelligence Platform.
> <https://doi.org/10.5281/zenodo.22923919>

That concept DOI always resolves to the newest version; `CITATION.cff` in the
repository has the per-version DOIs.

## Where the types come from

`src/ucip/models.py` is generated from `clients/openapi.json`, the same spec
artifact the TypeScript client is generated from, which is emitted from the
module the API serves its spec from. CI regenerates and diffs, so an API change
that is not reflected in these models fails the build.

Do not edit `models.py`. Change the spec and run `python scripts/generate.py`.

## Development

```bash
pip install -e ".[dev]"
python scripts/generate.py            # rebuild models.py from the spec
python -m pytest tests/               # stubbed transport, no network
UCIP_LIVE=1 python -m pytest tests/   # also run against the deployment
```

## Licence

Apache-2.0. The data has its own per-source terms: see
<https://uciplatform.vercel.app/legal>.
