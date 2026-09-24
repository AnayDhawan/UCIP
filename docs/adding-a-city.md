# Adding a city

UCIP's pipeline is city-agnostic: everything city-specific lives in one JSON
file, and every stage reads it. This page is how to stand up a new one.

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

Use the scaffolder. It derives the values that are dangerous to copy:

```bash
python pipeline/new_city.py \
  --slug pune --name Pune \
  --bbox 73.7 18.4 74.0 18.65 \
  --boundaries pune_wards.geojson --ward-id-field name \
  --expected-ward-count 15 --country India
```

That writes a config which passes `validate_cities.py` with no hand-editing.
Two fields in particular are derived rather than inherited:

- `grid.projected_crs`, the UTM zone for your bounding box. Copying Mumbai's
  leaves a city in the wrong zone, which distorts every area and distance in the
  pipeline while still producing output that looks fine.
- `map.center`, in Leaflet's `[lat, lon]` order, which is the reverse of the
  bbox's own order.

`ecology.calibrated` is written as `false` on purpose and the scaffolder will
not set it otherwise. See section 5 below for what changing it commits you to.

If you would rather write it by hand, copy `config/cities/mumbai.json` to
`config/cities/<slug>.json` and edit it. Every field is documented in
[`config/city.schema.json`](../config/city.schema.json), and
`python pipeline/validate_cities.py --city <slug>` will tell you what is wrong
by name.

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

Only the default city and the default 1 km resolution write to
`frontend/public/`. Standing up a second city, or running an experimental
resolution, cannot swap out what the live dashboard serves.

Stage 01 needs no credentials, so run it first: it tells you within seconds
whether your boundaries and bbox agree.

## 4b. Grid resolution

`grid.cell_size_m` sets the analysis resolution and 1 km is the default. To try
a different one without editing the config:

```bash
python pipeline/run_pipeline.py --cell-size 500
```

A non-default resolution writes everything to its own directory,
`data/<slug>_500m/`, and never to `frontend/public/`. That isolation is the
point: a 500 m run leaves the published 1 km dataset exactly where it was,
whether it finishes or fails part way.

Mumbai has been run end to end at 500 m. What it costs, measured rather than
estimated:

| Resolution | Grid cells | Published cells | Per ward | Cell payload |
|---|---|---|---|---|
| 1 km | 547 | 541 | 23 | 2.0 MB |
| 500 m | 2019 | 1975 | 82 | 4.2 MB |
| 250 m | 7726 | not run | 322 | not measured |

500 m is 3.7 times the cells rather than 4, because a large part of the bounding
box is sea and gets clipped away, and 2.1 times the bytes rather than 3.7,
because a smaller cell has a shorter boundary to encode.

Earth Engine's zonal reduction is the expensive call in a refresh and it runs
once per cell: stage 02 took 88 seconds at 500 m against roughly 25 at 1 km.
That is not the binding constraint. The browser payload is, and it is why 1 km
remains the default.

**500 m is not a strictly better dataset.** Eight of the 24 wards change rank,
and ward B moves from 6th to 1st. That is not a bug in either run: every ward's
500 m rank falls inside that ward's own 95% bootstrap interval from the 1 km
data (`pipeline/uncertainty.py`, issue #87), so the two resolutions agree, to
within the uncertainty the 1 km data already reported. It does mean a published
ranking is sensitive to a modelling choice, and switching resolution would
reshuffle the top of the table without making it more correct.

Anything that reports these ranks should read
[`docs/methodology.md`](methodology.md) on what they do and do not support.

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

**The full procedure is in [`calibrating-ecology.md`](calibrating-ecology.md)**,
which goes through each of the three assumptions the filter makes, why each is
Mumbai-specific, and how to decide for your city. The short version:

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
