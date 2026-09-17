# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-09-18

First tagged release. Nothing below is new work done for the tag; it's everything built
since the project started, with a version number finally attached to it. The "Aug 8, 2026
submission" line that used to sit here is gone because that deadline came and went and the
project kept going past it.

### Added
- A fourth map layer on the dashboard, Heat grid, draws the 541-cell HVI grid directly.
  The grid was already computed and already served over `/api/v1/cells`; only the map
  itself was ward-polygons-only before this. Clicking a cell selects its parent ward, same
  as clicking a ward polygon does.
- The site now says how old its data is: a "Data vintage" note on /methodology and a
  footer bar on the dashboard show the last pipeline-refresh date alongside the dry-season
  imagery window it was computed from (surfaced from the pipeline run log via
  /api/v1/meta; issue #124). The pipeline run log now records that window and is mirrored
  to `frontend/public/`, so the note updates itself on every refresh.
- Find-my-ward on the dashboard: a locate button on the map resolves the visitor's
  position to the BMC ward containing it via /api/v1/lookup, one tap after arrival (no
  permission prompt on load), with graceful handling of denial, unavailability, timeout
  and positions outside Mumbai (issue #116).
- End-to-end data pipeline: dry-season Landsat 8/9 LST + NDVI composite, WorldPop
  population/elderly layer (pinned to the 2020 vintage), OSM hospital distance, Datameet
  ward + slum-cluster boundaries.
- Heat Vulnerability Index (HVI), computed per grid cell and rolled up to the 24 BMC wards.
- Nature-based solutions (NBS) recommendation engine with an ecological-suitability check
  (Bastin/Veldman 2019) that can reject afforestation in favor of cool roofs or cooling
  centres, each recommendation cited to a peer-reviewed source.
- Next.js frontend: Leaflet choropleth (heat vulnerability, plantability, green-cover
  change layers), master-detail dashboard (ranked ward list + per-ward breakdown, synced
  through the URL), fullscreen map mode with a themed ward-info popup, methodology page
  with every weight and data source cited.
- Sensitivity analysis: top-ward ranking verified stable under +/-20% weight perturbation.
- Apache-2.0 license, full brand/design system (Inter + JetBrains Mono, teal/emerald
  tokens), light and dark themes.
- `pipeline/run_pipeline.py`: an orchestrated runner that chains all 13 pipeline stages
  in dependency order, stopping on the first hard failure and logging a structured
  run report, so a data refresh is one command instead of running each stage by hand.
- `.github/workflows/pipeline-refresh.yml`: a monthly GitHub Actions cron that runs the
  orchestrated pipeline and opens a PR with the refreshed data, matching the cadence
  documented in `pipeline/README.md` (satellite/demographic data does not change daily;
  live weather already updates independently via `frontend/src/lib/weather.ts`).
- `pipeline/diff_snapshots.py`: a diff-computation step that compares two pipeline runs'
  output and reports per-ward HVI rank shifts, NBS recommendation changes, and
  green-cover classification flips, with unit tests under `pipeline/tests/`.
- `docs/HVI-methodology-report.md`: a standalone technical report expanding the existing
  methodology and citation docs into a full writeup (PCA weighting, sensitivity
  analysis, plantability filter, limitations, references).

### Fixed
- Missing `python-dotenv` and `scipy` in `pipeline/requirements.txt` (used by
  `07_load.py` and `08_sensitivity.py` respectively, but not previously listed).
- Dashboard sidebar scroll, fullscreen popup theming in dark mode, ward search matching
  by locality name as well as ward code.
- A maintainer-facing proofreading note ("did you validate these literature weights for
  Mumbai?") was shipping on the live `/methodology` page, addressed to whoever read it as
  if they were the maintainer. Removed.
- The `/simulate` sliders accepted physically impossible inputs: up to 100% canopy
  conversion and 100% pocket-park conversion. Clamped to the range the underlying
  literature (Ziter et al.) actually covers, grounded in the 24 wards' real
  impervious-surface data instead of an arbitrary ceiling.

### Known limitations

Stated here instead of only on the methodology page, because a changelog is where people
check what changed before they trust a number, and burying the caveats where nobody reads
them first is its own kind of dishonesty.

- The land-surface-to-air-temperature relationship is validated against two weather
  stations, the only long-record NOAA GSOD sites in Mumbai (`data/lst_validation.json`).
  Pooled Pearson r = 0.716 on anomalies about each station's own mean. That number says the
  satellite composite tracks real thermal variation instead of sensor noise. It does not
  say the LST layer converts into a temperature you could read off a thermometer; the
  bias between the two ranges from 3.4°C to 13.9°C depending on what the ground is made of,
  and no single correction fixes that.
- Land surface temperature is daytime only, one dry-season composite. Nighttime heat is
  what actually drives heat mortality, and this pipeline does not touch it.
- Every HVI number is a point estimate. There is no uncertainty band anywhere, so a ward
  ranked 3rd and a ward ranked 5th might not be meaningfully different and the site
  currently has no way to tell you that.
- HVI measures vulnerability per ward, not people exposed. It is not population-weighted,
  so a small high-vulnerability ward and a large one read identically.
- No forecast coupling, no alert delivery, no municipal counterparty on the other end.
  This is a dataset meant to be cited, not an early-warning system, and it does not claim
  to be one anywhere in the app.
- `pipeline/14_timeseries.py` and `pipeline/15_optimize.py` run and produce real, committed
  output (`ward_timeseries.json`, `budget_allocation.json`). Neither is wired into
  `run_pipeline.py`'s orchestrated stage list or read by anything the live site or API
  serves. The numbers are real, they're just not reachable from anywhere a visitor would
  find them.
- `supabase/migrations/0006_postgis_geometry.sql` is written. `/api/v1/lookup` prefers it
  and falls back to a JavaScript point-in-polygon test when it isn't applied, so the
  endpoint works either way, but whether that migration is actually running against the
  live database is not something a changelog entry can confirm from a repo checkout alone.
- `.github/workflows/pipeline-refresh.yml` has a monthly schedule and has never executed
  against real Earth Engine or Supabase credentials. It exists and is wired up; nobody has
  watched it run.
- 30 open issues as of this tag. Most are scoped, real work, not noise, and this release
  does not pretend the backlog is empty.
