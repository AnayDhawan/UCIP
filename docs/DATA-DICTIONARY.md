# UCIP Data Dictionary

One place that defines what every dataset column and published file means: unit, valid range, source dataset, how it was derived, and known limitations. If a figure appears on the site, in the API, or in the published dataset, its definition belongs here or it is not finished.

Scope: the **Mumbai dataset** (24 BMC wards, 1 km grid, 541 complete cells). The pipeline reads its city from a config (issue #68); Pune is configured as a test case but has not been run end to end.

## Where the data lives

The pipeline (see `pipeline/README.md`) writes to **three places** from the same run:

| Store | Path | Used by |
|---|---|---|
| `data/` | repo root | The canonical dataset. The automated refresh PR commits it; `docs/api.md`'s release work reads it. |
| `frontend/public/` | mirror of the files the browser fetches | The site, at runtime. Every browser-fetched output is copied here by its stage (`_publish.py`); see pipeline/README.md's "Frontend sync" table. |
| Supabase | `wards`, `grid_cells`, `nbs_recommendations`, `interventions`, `methodology_refs` (migrations `0001`-`0010`) | The API's live source when configured; falls back to the committed snapshots when it is not. |

The public API (`/api/v1/*`) serves the same numbers from the database or the committed `frontend/public/` snapshots, carrying a `source` field of `database` or `snapshot`.

Unless stated otherwise: geometry is **WGS84 (EPSG:4326)** with coordinates ordered `[longitude, latitude]`; ward codes are BMC split-ward codes (`A`-`T`, with `F/N`, `G/S` style parts); all `*_pct` columns are on a **0-100 scale, not 0-1**.

**Refresh vintage:** a scheduled refresh re-pulls the inputs twice a week, but within a dry season they do not change, and several layers are single snapshots pinned by design (WorldPop 2020, the 2021 WorldCover epoch, current OpenStreetMap). `data/pipeline_run_log.json` records when a run happened and which dry-season Landsat window it used (see below). The dry-season window is Nov-Feb (Mumbai's monsoon imagery is unusable for LST).

## The HVI indicators (per grid cell)

The five scored indicators, all from free, open, global data (decision 2026-10-17; the set is defined once in `pipeline/_indicators.py`). Defined over every 1 km cell, then standardised and weighted in stage 05. Ranges quoted are those observed in the current 541-cell Mumbai run (verified in `pipeline/10_ward_profile.py`).

| Column | Unit | Valid / observed range | Source dataset | Derived | Known limitations |
|---|---|---|---|---|---|
| `LST_C` | degrees Celsius | observed 26.2-39.9 | Landsat 8/9 Collection 2 Level 2, `ST_B10`, dry-season median composite | Cloud-masked median over the dry-season window (Nov-Feb), 30 m reduced per cell | **Land-surface, not air, temperature** (radiometric ground temperature). Validated against GSOD stations in stage 13. |
| `NDVI` | index, unitless | −1 to 1; observed −0.07 to 0.71 | Landsat 8/9 C2 L2, `SR_B5`/`SR_B4` | Dry-season median `(NIR − red)/(NIR + red)` | A vegetation index, **not a canopy percentage**. |
| `pop_density_km2` | people / km² | ≥ 0; observed 16-115,272 | WorldPop 100 m, 2020 India image (age-sex collection, all bands summed), via Earth Engine | Summed population per cell / cell area | **Modelled surface, pinned to the 2020 WorldPop vintage**, not a census count; does not vary annually. |
| `hospital_dist_m` | metres | ≥ 0; observed 3.86-6,199 | OpenStreetMap hospitals via osmnx | Straight-line distance from cell centroid to nearest hospital | **Euclidean, not network** distance: a river or rail line in between is not accounted for. Current OSM data, not static. On the first principal component it runs against the other four (hot, dense cells sit close to hospitals); the index keeps the literature's direction. |
| `impervious_pct` | percent (0-100) | 0-100; observed 0.00-96.79 | ESA WorldCover v200 (2021) | Built-up share per cell from WorldCover class 50 (10 m) | Single WorldCover epoch; does not vary annually. |

## Context columns (per grid cell, not scored)

Carried through to the published cells so a reader can see them, but never standardised, weighted or summed into the index. Both were scored until 2026-10-17 and were taken out because neither exists for most cities or gets updated.

| Column | Unit | Observed range | Source dataset | Derived | Why not scored |
|---|---|---|---|---|---|
| `slum_pct` | percent (0-100) | 0.00-68.55 | Datameet slum-cluster polygons | Share of cell area covered by mapped slum clusters | A one-off Mumbai digitisation that is never updated. Mapped clusters, not a slum census: in a city with a layer, any cell with no mapped cluster reads 0. A city with no slum layer has null for every cell, which means no data. On `/cells` and `/export`. |
| `child_pct` | percent (0-100) | 6.75-13.09 | Census of India 2011 Primary Census Abstract, Census-ward level, republished by OpenCity | Population aged 0-6 / total population per BMC ward, assigned to every cell in the ward | Fifteen years old, Mumbai-only, and flat within a ward. Built by `pipeline/build_census_table.py`. On `/export` only. |

`NDVI_prev` (the green-cover baseline, used only for the change layer) is the same NDVI composite over a dry-season window ~9 years earlier so seasons are comparable.

## Per-cell derived fields

| Column | Meaning | Notes |
|---|---|---|
| `grid_id` | Cell identifier | String of the form `cell_NNNN` in the committed GeoJSON (`01_grid.py`) and in the database (text). |
| `ward_id`, `ward_gid` | Containing ward | Datameet BMC boundaries (`ward_gid` is the source id; `ward_id` is the split-ward code used everywhere in the UI/API). |
| `area_m2` | Cell area | Database only. |
| `worldcover_share` | Fraction of the cell's WorldCover pixels in `worldcover_class` | 0 to 1. Added for #168; absent from data produced before it. |
| `worldcover_mixed` | Whether that share is below 0.5 | True means no class is a majority, so `worldcover_class` (and the `plantable` flag that follows it) rests on a near-tie. Flagged, not reclassified. |
| `worldcover_class` | ESA WorldCover class code of the cell, the most common class by pixel count | Codes follow WorldCover (50 = built-up, 30 = herbaceous/grassland, 80/90 = water/wetland, 10/20 = trees/shrubs). |
| `plantable` | Whether the cell ecologically qualifies for tree planting | `true` only where restoration is supported: not water/wetland/mangrove/built-up, **not native grassland (class 30)**, and `impervious_pct` below the run's 75th percentile. Non-plantable hot cells get non-tree cooling instead (stage 06, Bastin 2019 constrained by Veldman 2019). |
| `hvi` | Heat Vulnerability Index, 0-100 | Z-scored indicators, oriented so higher = more vulnerable, PCA-weighted per Reid et al. 2009, rescaled 0-100. Higher = more vulnerable. |
| `contrib_*` (×5) | Per-factor contribution = weight × z-score, one per scored indicator | The explainability layer: a ward/cell score decomposes exactly into these. Mostly within ±0.3. Named `contrib_<indicator>`, e.g. `contrib_LST_C`. |
| `ndvi_delta` | `NDVI − NDVI_prev` | Stage 09, same-season comparison. |
| `lst_clear_obs` | Mean cloud-free Landsat observations per pixel backing this cell's LST | Stage 02. Cloud and shadow are masked before counting, so this is usable imagery, not passes. A dry-season window is roughly 8-16 passes; a cell in low single figures is persistently clouded. |
| `lst_obs_sparse` | `true` when `lst_clear_obs` < 3 | The cell's LST rests on too little imagery to trust. **Flagged, not dropped**: dropping would change the cell count between runs, which downstream stages and the quality gate treat as a stable property of the grid. Exclude these cells yourself if your analysis needs to. |
| `change_class` | `gained` / `stable` / `lost` / `unknown` | ΔNDVI classified with ±0.05 cutoffs (`stable` within ±0.05); `unknown` where either composite is missing. |

## Per-ward outputs

### `wards_hvi.geojson` (and the DB `wards` table)

One feature per ward (`FeatureCollection`). Properties:

| Field | Meaning |
|---|---|
| `ward_id`, `ward_gid` | See above. |
| `HVI` | Mean of member cells' HVI, 0-100. |
| `rank` | 1 = most vulnerable of the 24. |
| `n_cells` | Number of grid cells inside the ward. |
| `contrib_*` (×5) | Ward-level mean of the cell contributions. |
| `dominant_factor` | Indicator with the largest **absolute** contribution. Magnitude, not sign: a factor pushing the score down hard is driving it as much as one pushing it up. Null only if every contribution is zero. |
| `dominant_share` | That indicator's share of the ward's total absolute contribution, 0-1. An even spread across the five is 0.2. On the current Mumbai data the range is 0.22-0.47. |
| `single_factor_dominated` | True when `dominant_share` ≥ 0.5, i.e. one indicator accounts for half or more of the movement in the score. Such a ward needs a different intervention from one scoring high across all five. **No Mumbai ward currently crosses this**, which is itself a result: the index is not being carried by a single indicator anywhere. Threshold: `DOMINANCE_THRESHOLD` in `pipeline/_hvi.py`. |

### `ward_profiles.json` (`pipeline/10_ward_profile.py`)

Additive descriptive layer for the dashboard's ward dialog: it reads the outputs above and recomputes nothing. One object per ward with the scored indicators' ward means, each with a `_delta_city` companion (ward value minus city mean), plus:

| Field | Meaning |
|---|---|
| `percentile` | Ward's HVI percentile among the 24 (0-100). |
| `top_driver`, `top_driver_contrib` | The indicator contributing most to this ward's score, and its contribution value. |
| `neighbours` | Contiguous wards (from the boundary file, not distance). |
| `coolest_neighbour`, `hottest_neighbour` | `{ward_id, hvi}` of the coolest/hottest contiguous ward. |

Top-level: `generated_from`, `n_cells`, `n_wards`, `indicators` (canonical order), `units` (plain-language units per indicator), `city` (city means incl. `hvi_mean`).

### `nbs_recommendations.json`

Per-ward ranked recommendations (`pipeline/06_nbs.py` rule engine). Fields: `ward_id`, `intervention` (one of the `interventions` table names), `rationale` (plain-language, references the fired rule), `citation` (short name; see `docs/references.md`), `priority` (1 = highest within that ward), `cell_count` (cells the recommendation applies to). A ward can have several recommendations at the same priority.

### `ward_timeseries.json` (`pipeline/14_timeseries.py`)

**Not a multi-year HVI**, as the file itself states (`what_this_is` / `what_this_is_not`): only LST and NDVI are observed annually. Shape:

| Field | Meaning |
|---|---|
| `city`, `years`, `years_skipped`, `scenes_per_year`, `n_wards` | Run provenance; which years have usable dry-season coverage and how many Landsat scenes each used. |
| `measures` | `["LST_C", "NDVI"]`. |
| `wards` | Per ward: `ward_id`, `n_years`, `series` (`{year, LST_C, NDVI}` per dry season). |
| `summary` | Per-ward least-squares slope and classification for each measure. |
| `what_this_is`, `what_this_is_not`, `limitations` | Honest framing; the other three index indicators are snapshots, so only the thermal/vegetation trend is published. |

### `hvi_uncertainty.json` (`pipeline/uncertainty.py`)

95% bootstrap intervals for every ward's score and rank (issue #87). Fields:
`method`, `captures`, `does_not_capture`, `replicates`, `seed`, `confidence`,
`summary` (`median_rank_interval_width`, `widest_rank_interval`,
`wards_whose_rank_is_certain`, `n_wards`), and `per_ward` (`ward_id`, `hvi`,
`hvi_ci_low`, `hvi_ci_high`, `rank`, `rank_ci_low`, `rank_ci_high`).

`hvi` and `rank` are the published point estimates and match `wards_hvi.geojson`
exactly. The intervals come from resampling the 541 cells with replacement and
rerunning the whole scoring chain, so they reflect sampling uncertainty in the
cells and nothing else. **No ward's rank is certain**: the median interval spans
6 places. Treat the ranking as bands, not an order.

### `weighting_comparison.json` (`pipeline/compare_weightings.py`)

The ward ranking under the PCA-derived weights against the equal weighting the
pipeline falls back to (issue #88). Fields: `question`,
`weightings` (each with `source` and `weights`), `agreement` (`kendall_tau`,
`spearman_rho`, `wards_with_identical_rank`, `max_abs_rank_shift`,
`max_shift_ward`, `top_5_overlap`, and both top-5 lists), `ablation` (the same comparison with the lowest-weighted indicator dropped and both schemes refitted), `interpretation`, and
`per_ward` (`ward_id`, `rank_pca`, `rank_published`, `rank_shift`).

`rank_shift` is published minus PCA, so a positive value means the published
weighting ranks that ward as *less* vulnerable. The shifts sum to zero by
construction, since both are orderings of the same 24 wards.

### `hvi_pca_log.json`

PCA provenance for the current run: `loadings_pc1`, `explained_variance_pc1`, `weights` (normalised), `weight_source` (`pca_reid2009` or `fallback_equal_reid2009`), `fallback_used`, `fallback_trigger`. The published weights change only via this log.

### `sensitivity.json`

Weight-perturbation stability audit (stage 08): `baseline_top5`, `perturbation_pct` (0.2), `n_runs`, `mean_kendall_tau`, `mean_top5_overlap`, `all_top5_stable`, and one entry per run (`indicator`, `perturbation`, `kendall_tau`, `top5_overlap`, `top5_ranking`).

### `lst_validation.json`

Satellite-vs-station validation (stage 13): `window`, **`is_pipeline_window` (false: the validation uses a window with both satellite and station coverage, not the index window)**, `method`, `interpretation`, `limitations`, per-station `stations[]`, `pooled_within_station` (Pearson r, n). The expected LST↔air-temperature bias is positive and is not an error; the correlation is the figure that matters.

### `budget_allocation.json`

Illustrative budget-allocation model (stage 15, issue #67): `city`, the chosen `intervention` (with `cost` in `INR_per_m2` and `sourced_cost` / `source` / `source_url`, gated on sourced costs), `budget_inr`, `spent_inr`, `unspent_inr`, `wards_funded` / `wards_fully_funded`, `total_benefit_person_degrees`, `objective`, and the per-ward allocation. `illustrative_only` is false only when the cost is sourced.

### Earth Engine result cache (`pipeline/cache/gee/`, not committed)

Zonal statistics from stage 02, keyed by everything that can change them
(issue #93): region bounds, both date windows, the collection ids, the reducer
scale, the cloud threshold, and a fingerprint of the grid's ids and geometry.

A hit skips the `reduceRegions` call entirely, which is the expensive part of a
refresh. Within a dry season the composite window is fixed, so the twice-weekly
refresh pays Earth Engine once per season rather than twice a week.

There is no expiry. The key already changes when anything affecting the result
changes, so a time-to-live would only expire valid entries or serve stale ones.
`python 02_gee_layers.py --no-cache` forces a refetch.

### Per-stage provenance (inside `pipeline_run_log.json`)

Each stage entry may carry a `provenance` object recording what that stage
actually used and produced (issue #92), so a published figure can be traced
back to the imagery behind it rather than to a claim in a document. Stages
write these to `data/provenance/<id>.json` and the runner folds them in.

| Stage | Records |
|---|---|
| `01` | boundary file, wards in, cells out, cell size, projected CRS |
| `02` | Landsat and WorldCover collection ids, the composite window **actually queried**, scene counts for the current and previous windows, cells in/out, cells with an LST reading, GEE project |
| `04` | cells in/out, the columns produced |
| `05` | cells in, wards out, weight source, PC1 explained variance, whether the equal-weights fallback fired, the indicator list |
| `06` | WorldCover collection id, cells in, cells plantable, cells with a recommendation, the percentile thresholds used |

The key is absent rather than empty for a stage that records nothing, so the
log does not imply a stage was asked and had no answer. Recording is
best-effort by design: a stage that computes correct data and fails to describe
itself still publishes.

### `pipeline_run_log.json` (`pipeline/run_pipeline.py`)

What the last refresh actually did, and the site's data-age statement (issue #124): `started_at`, `finished_at` (UTC ISO 8601), `composite_window` (`{start, end}`: the dry-season Landsat window the run's figures were computed from), and `stages[]` (`id`, `script`, `cadence`, `status` ok/warn/fail/skipped, `returncode`, `seconds`). Mirrored to `frontend/public/` so `/api/v1/meta` and the site can read it. Committed with each refresh.

## Grid and boundary files

- `data/bmc_wards.geojson`: Datameet BMC ward boundaries (EPSG:4326), 24 wards, the geometry source of truth; `ward_gid`/`ward_id` originate here. BMC has since opened K North (split from K/E) and reportedly split P North; no open boundary file for the new wards exists yet.
- `data/slumClusters.geojson`: mapped Datameet slum-cluster polygons (input to the `slum_pct` context column).
- `data/grid_1km*.geojson`, `data/cells.geojson`, `data/cells_hvi.geojson`: pipeline intermediates; `cells.geojson` is the tidy per-cell indicator table.
- `data/hero_city.json`, `data/hero_region.json`: the landing page's 3D model geometry in **model space** (EPSG:32643 UTM 43N projected + scaled; see each file's `projection`, `space`, and `note`), *not* georeferenced coordinates. `generated_from` names the source files.
- `data/wards_hvi.geojson` / `cells_nbs.geojson` / `cells_ndvi_change.geojson` / `nbs_recommendations.json` / `ward_profiles.json` / `ward_timeseries.json` / `sensitivity.json` + `sensitivity_chart.png` / `lst_validation.json` / `hvi_pca_log.json` / `budget_allocation.json`: as above; the browser-fetched copies live in `frontend/public/`.

## Database notes

- Tables mirror the snapshots; the authoritative geometry is `geom_geojson jsonb` with native PostGIS `geom` added in migration 0006 (ward `geometry(MultiPolygon, 4326)`, cell `geometry(Polygon, 4326)`, GiST-indexed) for the `ward_at(lat, lon)` lookup.
- Bounded-score constraints (`0002`/`0004`): HVI 0-100 everywhere; `slum_pct`, `impervious_pct` 0-100 (`elderly_pct` was dropped in `0008`); ranks and priorities positive; not-null FKs tightened in `0003`.
- All writes go through the pipeline's service role; the anon key is read-only under the RLS policies in `0005` (verified by attempting anon INSERT/UPDATE/DELETE).

## Cross-cutting honesty notes

- There is no elderly indicator. `elderly_pct` and its `contrib_elderly_pct` were removed because the only source, WorldPop's India age-sex product, carries district age structure and not a ward-level measurement (methodology.md §10a).
- Neither age nor informal housing is scored. `child_pct` and `slum_pct` are context columns since 2026-10-17, so wards with large informal populations may rank lower than their real vulnerability.
- `slum_pct` is a **mapped proxy**, not a slum census, and is named as such everywhere it surfaces.
- `child_source` records where a cell's age structure came from, so a change of source is visible per cell rather than silently blended into the same column.
- LST is **land-surface temperature**, not air temperature; the dashboard copy says "about 3.1 C hotter than the city average" from LST, not a weather reading.
- `hospital_dist_m` is Euclidean; `slum_pct` treats unmapped areas as zero where a layer exists, and is null everywhere where none does.
- Scale traps: `*_pct` is 0-100 (not 0-1); NDVI is an index (not percent); HVI is ordinal-ish 0-100 and should be compared as ranks, not ratio differences.
- Anything not listed here that ships in a snapshot, the database, or the API is a gap in this dictionary: add it before it ships.
