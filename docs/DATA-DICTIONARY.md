# UCIP Data Dictionary

One place that defines what every dataset column and published file means: unit, valid range, source dataset, how it was derived, and known limitations. If a figure appears on the site, in the API, or in the published dataset, its definition belongs here or it is not finished.

Scope: the **Mumbai dataset** (24 BMC wards, 1 km grid, 541 complete cells). The pipeline is city-agnostic (issue #68); a second city adds rows in the same schema, not new columns.

## Where the data lives

The pipeline (see `pipeline/README.md`) writes to **three places** from the same run:

| Store | Path | Used by |
|---|---|---|
| `data/` | repo root | The canonical dataset. The automated refresh PR commits it; `docs/api.md`'s release work reads it. |
| `frontend/public/` | mirror of the files the browser fetches | The site, at runtime. Every browser-fetched output is copied here by its stage (`_publish.py`); see pipeline/README.md's "Frontend sync" table. |
| Supabase | `wards`, `grid_cells`, `nbs_recommendations`, `interventions`, `methodology_refs` (migrations `0001`–`0006`) | The API's live source when configured; falls back to the committed snapshots when it is not. |

The public API (`/api/v1/*`) serves the same numbers from the database or the committed `frontend/public/` snapshots, carrying a `source` field of `database` or `snapshot`.

Unless stated otherwise: geometry is **WGS84 (EPSG:4326)** with coordinates ordered `[longitude, latitude]`; ward codes are BMC split-ward codes (`A`–`T`, with `F/N`, `G/S` style parts); all `*_pct` columns are on a **0–100 scale, not 0–1**.

**Refresh vintage:** the satellite and demographic inputs are re-pulled monthly; several layers are single snapshots pinned by design (WorldPop 2020, one Datameet slum snapshot, current OpenStreetMap, one WorldCover epoch). `data/pipeline_run_log.json` records when a run happened and which dry-season Landsat window it used (see below). The dry-season window is Nov–Feb (Mumbai's monsoon imagery is unusable for LST).

## The seven HVI indicators (per grid cell)

Defined over every 1 km cell, then standardised and weighted in stage 05. Ranges quoted are those observed in the current 541-cell Mumbai run (verified in `pipeline/10_ward_profile.py`).

| Column | Unit | Valid / observed range | Source dataset | Derived | Known limitations |
|---|---|---|---|---|---|
| `LST_C` | degrees Celsius | observed 26.2–39.9 | Landsat 8/9 Collection 2 Level 2, `ST_B10`, dry-season median composite | Cloud-masked median over the dry-season window (Nov–Feb), 30 m reduced per cell | **Land-surface, not air, temperature** (radiometric ground temperature). Validated against GSOD stations in stage 13. |
| `NDVI` | index, unitless | −1 to 1; observed −0.07 to 0.71 | Landsat 8/9 C2 L2, `SR_B5`/`SR_B4` | Dry-season median `(NIR − red)/(NIR + red)` | A vegetation index, **not a canopy percentage**. |
| `pop_density_km2` | people / km² | ≥ 0; observed 16–115,272 | WorldPop 100 m age-sex rasters via Earth Engine | Summed population per cell / cell area | **Modelled surface, pinned to the 2020 WorldPop vintage**, not a census count; does not vary annually. |
| `elderly_pct` | percent (0–100) | 0–100; observed 4.02–5.59 | WorldPop 100 m age-sex (60+), same surface | 60+ population ÷ total population per cell | **Proxy, not census.** Near-flat across the city (1.6 points total), so it separates wards very weakly; the UI must not lean on it. |
| `slum_pct` | percent (0–100) | 0–100; observed 0.00–68.55 | Datameet slum-cluster polygons | Share of cell area covered by mapped slum clusters | **Proxy**: mapped clusters, not a slum census; any cell with no mapped cluster reads 0. Real observed boundaries (preferred over the modelled GHS-SMOD proxy). |
| `hospital_dist_m` | metres | ≥ 0; observed 3.86–6,199 | OpenStreetMap hospitals via osmnx | Straight-line distance from cell centroid to nearest hospital | **Euclidean, not network** distance — a river or rail line in between is not accounted for. Current OSM snapshot, not static. |
| `impervious_pct` | percent (0–100) | 0–100; observed 0.00–96.79 | ESA WorldCover | Built-up share per cell from WorldCover class 50 (10 m) | Single WorldCover epoch; does not vary annually. |

`NDVI_prev` (the green-cover baseline, used only for the change layer) is the same NDVI composite over a dry-season window ~9 years earlier so seasons are comparable.

## Per-cell derived fields

| Column | Meaning | Notes |
|---|---|---|
| `grid_id` | Cell identifier | Numeric in the committed GeoJSON (`01_grid.py`); the database stores it as text `cell_0001`. |
| `ward_id`, `ward_gid` | Containing ward | Datameet BMC boundaries (`ward_gid` is the source id; `ward_id` is the split-ward code used everywhere in the UI/API). |
| `area_m2` | Cell area | Database only. |
| `worldcover_class` | ESA WorldCover class code of the cell | Codes follow WorldCover (50 = built-up, 30 = herbaceous/grassland, 80/90 = water/wetland, 10/20 = trees/shrubs). |
| `plantable` | Whether the cell ecologically qualifies for tree planting | `true` only where restoration is supported: not water/wetland/mangrove/built-up, **not native grassland (class 30)**, and `impervious_pct` below the run's 75th percentile. Non-plantable hot cells get non-tree cooling instead (stage 06, Bastin 2019 constrained by Veldman 2019). |
| `hvi` | Heat Vulnerability Index, 0–100 | Z-scored indicators, oriented so higher = more vulnerable, PCA-weighted per Reid et al. 2009, rescaled 0–100. Higher = more vulnerable. |
| `contrib_*` (×7) | Per-factor contribution = weight × z-score | The explainability layer: a ward/cell score decomposes exactly into these. Mostly within ±0.3. Named `contrib_<indicator>`, e.g. `contrib_LST_C`. |
| `ndvi_delta` | `NDVI − NDVI_prev` | Stage 09, same-season comparison. |
| `change_class` | `gained` / `stable` / `lost` / `unknown` | ΔNDVI classified with ±0.05 cutoffs (`stable` within ±0.05); `unknown` where either composite is missing. |

## Per-ward outputs

### `wards_hvi.geojson` (and the DB `wards` table)

One feature per ward (`FeatureCollection`). Properties:

| Field | Meaning |
|---|---|
| `ward_id`, `ward_gid` | See above. |
| `HVI` | Mean of member cells' HVI, 0–100. |
| `rank` | 1 = most vulnerable of the 24. |
| `n_cells` | Number of grid cells inside the ward. |
| `contrib_*` (×7) | Ward-level mean of the cell contributions. |

### `ward_profiles.json` (`pipeline/10_ward_profile.py`)

Additive descriptive layer for the dashboard's ward dialog — reads the outputs above, recomputes nothing. One object per ward with the seven indicators' ward means, each with a `_delta_city` companion (ward value minus city mean), plus:

| Field | Meaning |
|---|---|
| `percentile` | Ward's HVI percentile among the 24 (0–100). |
| `top_driver`, `top_driver_contrib` | The indicator contributing most to this ward's score, and its contribution value. |
| `neighbours` | Contiguous wards (from the boundary file, not distance). |
| `coolest_neighbour`, `hottest_neighbour` | `{ward_id, hvi}` of the coolest/hottest contiguous ward. |

Top-level: `generated_from`, `n_cells`, `n_wards`, `indicators` (canonical order), `units` (plain-language units per indicator), `city` (city means incl. `hvi_mean`).

### `nbs_recommendations.json`

Per-ward ranked recommendations (`pipeline/06_nbs.py` rule engine). Fields: `ward_id`, `intervention` (one of the `interventions` table names), `rationale` (plain-language, references the fired rule), `citation` (short name; see `docs/references.md`), `priority` (1 = highest within that ward), `cell_count` (cells the recommendation applies to). A ward can have several recommendations at the same priority.

### `ward_timeseries.json` (`pipeline/14_timeseries.py`)

**Not a multi-year HVI** — stated in the file itself (`what_this_is` / `what_this_is_not`): only LST and NDVI are observed annually. Shape:

| Field | Meaning |
|---|---|
| `city`, `years`, `years_skipped`, `scenes_per_year`, `n_wards` | Run provenance; which years have usable dry-season coverage and how many Landsat scenes each used. |
| `measures` | `["LST_C", "NDVI"]`. |
| `wards` | Per ward: `ward_id`, `n_years`, `series` (`{year, LST_C, NDVI}` per dry season). |
| `summary` | Per-ward least-squares slope and classification for each measure. |
| `what_this_is`, `what_this_is_not`, `limitations` | Honest framing; the other five index indicators are frozen snapshots, so only the thermal/vegetation trend is published. |

### `hvi_pca_log.json`

PCA provenance for the current run: `loadings_pc1`, `explained_variance_pc1`, `weights` (normalised), `weight_source` (`pca_reid2009` or `published_fallback`), `fallback_used`, `fallback_trigger`. The published weights change only via this log.

### `sensitivity.json`

Weight-perturbation stability audit (stage 08): `baseline_top5`, `perturbation_pct` (0.2), `n_runs`, `mean_kendall_tau`, `mean_top5_overlap`, `all_top5_stable`, and one entry per run (`indicator`, `perturbation`, `kendall_tau`, `top5_overlap`, `top5_ranking`).

### `lst_validation.json`

Satellite-vs-station validation (stage 13): `window`, **`is_pipeline_window` (false — the validation uses a window with both satellite and station coverage, not necessarily the index window)**, `method`, `interpretation`, `limitations`, per-station `stations[]`, `pooled_within_station` (Pearson r, n). The expected LST↔air-temperature bias is positive and is not an error; the correlation is the figure that matters.

### `budget_allocation.json`

Illustrative budget-allocation model (stage 15, issue #67): `city`, the chosen `intervention` (with `cost` in `INR_per_m2` and `sourced_cost` / `source` / `source_url` — gated on sourced costs), `budget_inr`, `spent_inr`, `unspent_inr`, `wards_funded` / `wards_fully_funded`, `total_benefit_person_degrees`, `objective`, and the per-ward allocation. `illustrative_only` is false only when the cost is sourced.

### `pipeline_run_log.json` (`pipeline/run_pipeline.py`)

What the last refresh actually did, and the site's data-age statement (issue #124): `started_at`, `finished_at` (UTC ISO 8601), `composite_window` (`{start, end}` — the dry-season Landsat window the run's figures were computed from), and `stages[]` (`id`, `script`, `cadence`, `status` ok/warn/fail/skipped, `returncode`, `seconds`). Mirrored to `frontend/public/` so `/api/v1/meta` and the site can read it; absent from the repo until a refresh commits one.

## Grid and boundary files

- `data/bmc_wards.geojson` — Datameet BMC ward boundaries (EPSG:4326), the geometry source of truth; `ward_gid`/`ward_id` originate here.
- `data/slumClusters.geojson` — mapped Datameet slum-cluster polygons (input to `slum_pct`).
- `data/grid_1km*.geojson`, `data/cells.geojson`, `data/cells_hvi.geojson` — pipeline intermediates; `cells.geojson` is the tidy seven-indicator table.
- `data/hero_city.json`, `data/hero_region.json` — the landing page's 3D model geometry in **model space** (EPSG:32643 UTM 43N projected + scaled; see each file's `projection`, `space`, and `note`), *not* georeferenced coordinates. `generated_from` names the source files.
- `data/wards_hvi.geojson` / `cells_nbs.geojson` / `cells_ndvi_change.geojson` / `nbs_recommendations.json` / `ward_profiles.json` / `ward_timeseries.json` / `sensitivity.json` + `sensitivity_chart.png` / `lst_validation.json` / `hvi_pca_log.json` / `budget_allocation.json` — as above; the browser-fetched copies live in `frontend/public/`.

## Database notes

- Tables mirror the snapshots; the authoritative geometry is `geom_geojson jsonb` with native PostGIS `geom` added in migration 0006 (ward `geometry(MultiPolygon, 4326)`, cell `geometry(Polygon, 4326)`, GiST-indexed) for the `ward_at(lat, lon)` lookup.
- Bounded-score constraints (`0002`/`0004`): HVI 0–100 everywhere; `elderly_pct`, `slum_pct`, `impervious_pct` 0–100; ranks and priorities positive; not-null FKs tightened in `0003`.
- All writes go through the pipeline's service role; the anon key is read-only under the RLS policies in `0005` (verified by attempting anon INSERT/UPDATE/DELETE).

## Cross-cutting honesty notes

- `elderly_pct` and `slum_pct` are **modelled or mapped proxies**, not ward-level census, and are named as such everywhere they surface (methodology page, UI copy, this file).
- LST is **land-surface temperature**, not air temperature; the dashboard copy says "about 3.1 C hotter than the city average" from LST, not a weather reading.
- `hospital_dist_m` is Euclidean; `slum_pct` treats unmapped areas as zero.
- Scale traps: `*_pct` is 0–100 (not 0–1); NDVI is an index (not percent); HVI is ordinal-ish 0–100 and should be compared as ranks, not ratio differences.
- Anything not listed here that ships in a snapshot, the database, or the API is a gap in this dictionary — add it before it ships.
