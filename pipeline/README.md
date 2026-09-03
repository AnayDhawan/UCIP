# Pipeline

Thirteen numbered stages (`00_gee_spike.py` through `12_hero_region.py`) that turn raw
satellite imagery, WorldPop demographics, and OSM/Datameet vector data into the Heat
Vulnerability Index, the NBS recommendations, and every JSON/GeoJSON file the frontend
reads. Each script is documented in its own docstring and is still runnable standalone;
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

`run_pipeline.py` (issue #56) runs stages `01` through `12` in dependency order, stops at
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
| `run_pipeline.py` | `pipeline_run_log.json` | yes |

The `run_pipeline.py` row is the orchestrator's own run log rather than a stage output:
the dashboard footer and `/api/v1/meta` read it from `frontend/public/` (issue #124), and
it rides the same automated refresh PR as every other file in the table.

`sensitivity.json`, `hvi_pca_log.json` and `pipeline_run_log.json` are the exceptions to
"the deployed frontend reads from `frontend/public/`": the methodology page reads all
three server-side straight out of `../data/`, so they need no copy for that page — but
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

**Every stage below runs on a monthly cadence, not daily, because the data underneath
it does not change daily.**

| Stage | Cadence | Why |
|-------|---------|-----|
| `01_grid.py` | Monthly | BMC ward boundaries are static; only changes if `data/bmc_wards.geojson` is re-sourced. |
| `02_gee_layers.py` | Monthly | Landsat 8/9 dry-season **composite** (`00_gee_spike.py`'s validated recipe), a multi-week median composite by construction, not a daily reading. |
| `03_vectors.py` | Monthly | WorldPop's age-sex layer is pinned to a single annual vintage (`WORLDPOP_YEAR = "2020"`, see the script); OSM hospitals and slum-cluster boundaries change on the order of months, not days. |
| `04_zonal.py` | Monthly | Pure consolidation of the two stages above; has nothing new to compute between their refreshes. |
| `05_hvi.py` | Monthly | Deterministic function of `04`'s output; the PCA weights themselves are also expected to be stable run-to-run (see `docs/HVI-methodology-report.md` section 6, the sensitivity analysis). |
| `06_nbs.py` | Monthly | Its GEE call is ESA WorldCover, an annual-cadence land-cover product. |
| `07_load.py` | Monthly | Terminal upsert/snapshot step of the same refresh; runs once per chain, immediately after the stage that changed. |
| `08_sensitivity.py` | Monthly | Cheap function of `05`'s weights; nothing to recompute until `05` changes. |
| `09_ndvi_change.py` | Monthly | Function of `02`'s two NDVI composites (current vs. a ~9-year baseline); does not move month to month. |
| `10_ward_profile.py` | Monthly | Rolls up `05`/`06` output; changes only when they do. |
| `11_hero_city.py` | Monthly | Geometry + HVI/rank read from `05`; changes only when boundaries or HVI change. |
| `12_hero_region.py` | Monthly | Natural Earth coastline, effectively static; cached to `data/cache/` after the first fetch. |

Running this chain more often than monthly would re-fetch the same underlying
satellite/demographic snapshot and re-derive the same numbers, at real GEE-quota cost,
for a "last updated" timestamp with no real signal behind it: cosmetic freshness, not
actual freshness. A monthly cron (`.github/workflows/pipeline-refresh.yml`, issue #58)
matches the data's real cadence.

**The one genuinely fast-changing number in the product, live air temperature, is
intentionally not a pipeline stage at all.** `frontend/src/lib/weather.ts` fetches it
client-side from Open-Meteo on every page load: no server, no cron, no committed
snapshot, no staleness possible. That pattern (fetch live at request time, show an
honest "unavailable" state on failure, never fabricate or cache a stale number) is the
template for any future value that is actually fast-changing: extend `weather.ts`'s
approach for it, rather than adding another monthly-refreshed pipeline stage and
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
