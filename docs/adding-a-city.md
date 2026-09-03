# Adding a city

UCIP's pipeline is city-agnostic: everything city-specific lives in one JSON
file, and the twelve stages read it. This page is how to stand up a new one.

Be realistic about effort. This is a few hours of work plus a Google Cloud
project, not a five-minute setup, and the last section is the part most people
would rather skip and should not.

## What you need first

- **A Google Earth Engine account.** Free for research and non-commercial use,
  but approval is not instant. Everything up to stage 01 works without it; every
  satellite layer needs it.
- **Ward boundaries as GeoJSON**, one polygon per administrative unit, with a
  field holding each unit's name or code. For Indian cities
  [Datameet](https://github.com/datameet/Municipal_Spatial_Data) is the usual
  source. Elsewhere, OpenStreetMap administrative relations or GADM.
- **Python environment** per [`pipeline/README.md`](../pipeline/README.md).

## 1. Get the boundaries

Drop the file in `data/`. Then check what is actually in it, because the field
names vary by source and are the first thing to get wrong:

```python
import geopandas as gpd
g = gpd.read_file("data/pune_wards.geojson")
print(len(g), list(g.columns), g.crs)
print([round(v, 3) for v in g.total_bounds])   # min_lon, min_lat, max_lon, max_lat
```

## 2. Write the config

Copy `config/cities/mumbai.json` to `config/cities/<slug>.json` and edit it.
Every field is documented in [`config/city.schema.json`](../config/city.schema.json).

```json
{
  "slug": "pune",
  "name": "Pune",
  "timezone": "Asia/Kolkata",
  "bbox": [73.7, 18.4, 74.0, 18.65],
  "boundaries": {
    "file": "pune_wards.geojson",
    "ward_id_field": "name",
    "expected_ward_count": 15
  },
  "grid": { "cell_size_m": 1000 },
  "map": { "center": [18.5204, 73.8567], "zoom": 12 },
  "ecology": { "calibrated": false }
}
```

Three fields cause most of the mistakes:

- **`bbox` is `[min_lon, min_lat, max_lon, max_lat]`.** Take it from the
  boundary file's own bounds and round outward. It doubles as the plausibility
  check the grid stage validates its output against, so a bbox copied from
  another city fails loudly rather than silently.
- **`map.center` is `[lat, lon]`**, which is Leaflet's order and the reverse of
  GeoJSON's. Getting it backwards puts the map in the sea.
- **`grid.projected_crs` is optional and usually should be omitted.** Left out,
  the UTM zone is derived from the bbox centroid. Set it only for a city
  straddling a zone boundary, and know why you are setting it: an inherited UTM
  zone from another city silently distorts every area and distance in the
  pipeline while still producing output that looks entirely reasonable.

## 3. Validate before running anything

```bash
python pipeline/validate_cities.py --city pune
```

This checks the boundary file exists and parses, that the ward id field is
really there, that the ward count matches, that the boundaries fall inside your
bbox, and that the UTM zone suits the bbox. Thirty seconds here saves a
forty-minute Earth Engine run that fails at the end.

## 4. Run the pipeline

```bash
python pipeline/run_pipeline.py --city pune
```

Or one stage at a time while debugging:

```bash
python pipeline/01_grid.py --city pune
```

Output goes to `data/<slug>/`, so cities cannot overwrite each other. Mumbai is
the exception and writes to `data/` directly, because the site, the committed
snapshots and the deck all reference those paths.

Stage 01 needs no credentials, so run it first: it tells you within seconds
whether your boundaries and bbox agree.

## 5. Calibrate the ecology. Do not skip this.

This is the part that matters, and the part a config file cannot do for you.

**The plantability filter encodes Mumbai's ecology.** It treats ESA WorldCover
class 30 as native grassland to protect, and sets "high" and "low" cutoffs at
percentiles of Mumbai's own cells. The Heat Vulnerability Index is safer: its
PCA weights are recomputed from each city's own data automatically.

Applied unexamined to a different biome, the filter will confidently recommend
planting trees on habitat that should stay open. That is precisely the failure
[Veldman et al. 2019](https://doi.org/10.1126/science.aay7976) warns about in
their response to Bastin 2019, and refusing to make it is the thing that
distinguishes this project from a greening-is-always-good map. Getting it wrong
does not just make the output useless; it makes it harmful.

Pune is the worked example, and its config says `"calibrated": false` for exactly
this reason. The Deccan plateau has genuinely native grassland and scrub that
Mumbai's coastal thresholds were never designed to tell apart from degraded
land.

What to do:

1. Read the restoration and land-cover literature for the city's biome.
2. Decide which WorldCover classes are native open habitat there, not
   plantable land.
3. Re-examine the percentile cutoffs in `pipeline/06_nbs.py`. Percentiles are
   relative to the city's own cells, which travels better than absolute
   thresholds, but "relative to a uniformly dense city" and "relative to one
   with large open tracts" are not the same distribution.
4. Set `"calibrated": true` only once a person has actually done this.

`validate_cities.py` warns while the flag is false. That warning is doing its
job; do not silence it by flipping the flag.

## 6. Publish, if you want to

Serving a city on the site means importing its mirror in
`frontend/src/lib/city.ts` and switching `ACTIVE_CITY`. Run
`python pipeline/sync_city_config.py` first, which mirrors configs into the
frontend bundle; CI fails if that mirror is stale.

## Known limits

- **`data/slumClusters.geojson` is Mumbai-specific.** Stage 03 uses it for the
  slum indicator and falls back to zero for every cell without it, so another
  city currently loses that indicator entirely unless you supply an equivalent.
- **Hospital locations come from OpenStreetMap**, whose completeness varies a
  lot between cities. Sparse coverage silently weakens the access indicator.
- **WorldPop is pinned to a specific India image** in `pipeline/03_vectors.py`.
  A city outside India needs that changed.
- **The dry-season window is Mumbai's monsoon calendar** (November to February,
  in `pipeline/02_gee_layers.py`). A city with a different wet season needs
  different months, or the composites are built from cloud.

None of these are hidden in the code: each is a named constant with a comment
saying why it is what it is. But they are why "city-agnostic" means the
machinery generalises, not that the assumptions do.
