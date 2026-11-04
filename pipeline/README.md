# Pipeline

Sixteen numbered scripts (`00_gee_spike.py` through `15_optimize.py`) that turn
satellite imagery, WorldPop population, ESA WorldCover land cover and OpenStreetMap
hospitals into the Heat Vulnerability Index, the NBS recommendations, and every
JSON/GeoJSON file the frontend reads. `00` is a connectivity check and is skipped by
default; `14` (the year-by-year trend) runs only with `--include-annual`. Each script is documented in its own docstring and is still runnable standalone;
this page covers running them as one chain, and when that chain should actually run.

## Running a refresh

```bash
cd pipeline
python -m venv .venv
.venv\Scripts\activate      # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
earthengine authenticate    # once, needs your own Google Earth Engine account
cp ../.env.example ../.env.local   # fill in Supabase keys if you want the DB upsert too

python run_pipeline.py
```

`run_pipeline.py` (issue #56) runs stages `01` through `15` in dependency order, stops at
the first hard failure, and writes a run log to `data/pipeline_run_log.json` (mirrored to
`frontend/public/`; see "Frontend sync" below). The log records when the run happened and
the dry-season window it was computed from (issue #124), which is what the site's
"data vintage" note shows. Useful
flags:

| Flag | Effect |
|------|--------|
| `--dry-run` | Print the execution plan, run nothing. |
| `--from 05` | Resume the chain starting at stage `05` (after fixing a failure). |
| `--only 08,09` | Run just the listed stages. |
| `--include-spike` | Also run `00_gee_spike.py` first (excluded by default, see below). |
| `--include-annual` | Also run `14_timeseries.py`, the multi-year trend (about 13 minutes of Earth Engine time). |
| `--keep-going` | Don't stop the chain on a hard failure. |

`00_gee_spike.py` is a one-time development go/no-go gate, not a stage of a real
refresh: it queries a small fixed test bbox to sanity-check GEE connectivity and writes
nothing any later stage reads. It stays in the repo and in `run_pipeline.py`'s stage
list (so `--include-spike` can still run it, e.g. to smoke-test credentials in CI) but
is excluded from a plain `python run_pipeline.py`.

A stage script's exit code means: `0` clean pass, `2` ran but a sanity check flagged
"CHECK WARNINGS" (non-fatal, e.g. the PCA fallback triggering), `1` hard failure. The
runner stops the chain on `1` and continues past `2`.

## Frontend sync

A refresh is only real if the live site actually serves it. The deployed frontend
reads its data from `frontend/public/`, not from `data/` directly (see
`frontend/src/lib/useWardData.ts`, `frontend/src/app/components/WardChoropleth.tsx`,
and `frontend/src/app/page.tsx`), so every stage whose output the browser fetches at
runtime writes to both places in the same run, not just `data/`:

| Stage | Writes to `data/` | Also copies to `frontend/public/` |
|-------|--------------------|------------------------------------|
| `05_hvi.py` | `wards_hvi.geojson` | yes |
| `06_nbs.py` | `cells_nbs.geojson`, `nbs_recommendations.json` | yes, both |
| `08_sensitivity.py` | `sensitivity_chart.png` | yes |
| `09_ndvi_change.py` | `cells_ndvi_change.geojson` | yes |
| `10_ward_profile.py` | `ward_profiles.json` | yes (already did this before #56) |
| `11_hero_city.py` | `hero_city.json` | yes (already did this before #56) |
| `12_hero_region.py` | `hero_region.json` | yes (already did this before #56) |
| `13_validate_lst.py` | `lst_validation.json` | yes |
| `14_timeseries.py` | `ward_timeseries.json` | yes |
| `15_optimize.py` | `budget_allocation.json` | yes |
| `uncertainty.py` (run separately) | `hvi_uncertainty.json` | yes |
| `compare_weightings.py` (run separately) | `weighting_comparison.json` | yes |
| `run_pipeline.py` | `pipeline_run_log.json` | yes |

The `run_pipeline.py` row is the orchestrator's own run log rather than a stage output:
the dashboard footer and `/api/v1/meta` read it from `frontend/public/` (issue #124), and
it rides the same automated refresh PR as every other file in the table.

`sensitivity.json`, `hvi_pca_log.json` and `pipeline_run_log.json` are the exceptions to
"the deployed frontend reads from `frontend/public/`": the methodology page reads all
three server-side straight out of `../data/`, so they need no copy for that page. But
`pipeline_run_log.json` still gets one, because `/api/v1/meta` and the dashboard footer
(which are not the methodology page) read it from `frontend/public/` like every other
route does. `sensitivity_chart.png` is
different from `sensitivity.json` even though both come from `08_sensitivity.py`: the
chart is rendered as a plain `<img src="/sensitivity_chart.png">`, a browser-fetched
static asset, so it does need the copy.

Before this, only `10`-`12` copied their own output to `frontend/public/`; `05`, `06`,
`08`, and `09`'s outputs were kept in sync by a one-time hand copy when the repo was
first built, not by anything a refresh would repeat. A pipeline run would have quietly
kept writing correct data to `data/` while the live site kept serving whatever was
hand-copied into `frontend/public/` at that one point in time, indefinitely. All four
now copy their own output the same way `10`-`12` already did, so this can't recur
silently for any stage added later either, as long as it follows the same pattern.

**The copy runs AFTER each stage's own sanity check, and only if it passes.** `05`,
`06`, `08`, and `09` each already had an end-of-run sanity check (HVI range and ward
count, recommendation coverage, weight-perturbation stability, NDVI-unknown rate) that
flags a bad run with a `[WARN]`/exit-code-2 but doesn't stop `run_pipeline.py`'s chain.
A stage that produces genuinely bad data (fewer than 24 wards, unstable ranking, too
many "unknown" NDVI cells) writes that bad data to `data/` as always, but its
`frontend/public/` copy is skipped, with an explicit `[WARN]` saying so. The live site
keeps serving its previous (last-known-good) file instead of a broken run, with no
manual rollback needed. `pipeline/_publish.py`'s `publish(src, dest)` is the one place
this copy actually happens, called from each stage's `if ok:` branch.

## Refresh cadence (issue #57)

**The data underneath changes once a dry season at most. The scheduled workflow
(`.github/workflows/pipeline-refresh.yml`) runs twice a week anyway, on Tuesdays and
Fridays, by explicit request, so the published data is never more than a few days from a
verified run.** Within a dry season most of those runs reproduce identical numbers, and
the workflow opens nothing when the output is byte-identical. How often each stage's
input actually changes:

| Stage | Input changes | Why |
|-------|---------------|-----|
| `01_grid.py` | Rarely | Ward boundaries are static until `data/bmc_wards.geojson` is re-sourced. |
| `02_gee_layers.py` | Once a dry season | A Nov-Feb Landsat 8/9 median **composite**, fixed once the season is complete. |
| `03_vectors.py` | Months | WorldPop is pinned to one vintage (`WORLDPOP_YEAR = "2020"`); OSM hospitals change slowly. |
| `04_zonal.py` | With 02/03 | Pure consolidation of the two stages above. |
| `05_hvi.py` | With 04 | Deterministic function of `04`'s output. |
| `06_nbs.py` | With 05 | Its Earth Engine call is ESA WorldCover, a fixed 2021 epoch. |
| `07_load.py` | With 06 | Writes the snapshots, and loads the database when credentials are set. |
| `08_sensitivity.py` | With 05 | Function of `05`'s weights. |
| `09_ndvi_change.py` | Once a dry season | Current versus 2016-17 NDVI composite. |
| `10_ward_profile.py` | With 05/06 | Rolls up their output. |
| `11_hero_city.py` | With 05 | Geometry plus HVI/rank. |
| `12_hero_region.py` | Never | Natural Earth coastline, cached to `data/cache/` after the first fetch. |
| `13_validate_lst.py` | When NOAA publishes | Station data arrives with a lag. |
| `14_timeseries.py` | Once a year | One value per dry season. |
| `15_optimize.py` | With 05 | The worked budget scenario. |

**The fast-changing numbers in the product, live air temperature and the ward weather
forecast, are intentionally not pipeline stages at all.** `frontend/src/lib/weather.ts`
fetches them from Open-Meteo at request time: the home page strip calls it from the
browser on every page load, and the ward weather panel goes through the
`/api/weather/{ward}` route, whose responses are cacheable at the CDN for 30 minutes and
carry the reading time. There is no cron and no committed snapshot. That pattern (fetch
live at request time, show an honest "unavailable" state on failure, never fabricate a
number) is the template for any future value that is actually fast-changing: extend
`weather.ts`'s approach for it, rather than adding another scheduled pipeline stage and
labeling it "daily" for effect.

## Change diffing (issue #61)

`diff_snapshots.py` compares two runs' worth of pipeline output (a "before" directory
and an "after" directory, each holding `wards_hvi.geojson`, `nbs_recommendations.json`,
and `cells_ndvi_change.geojson`) and reports, per ward: HVI rank shifts, NBS
recommendations added/removed, and green-cover classification flips. It is a plain
diff over pipeline artifacts, with no notion of user accounts or saved wards. See the
script's own docstring and the PR description for what is and is not in scope.

Each of the three categories is only diffed if its own file existed in the "before"
directory (`had_rank_baseline`/`had_nbs_baseline`/`had_green_cover_baseline` in the
output), independently of the other two. A partial "before" directory, e.g. an
interrupted first refresh, reports the categories it has no baseline for as not-diffed
rather than as a false wall of changes for every ward.

```bash
python diff_snapshots.py --old-dir /path/to/previous/data --new-dir ../data --out ../data/pipeline_diff.json
```
