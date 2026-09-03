# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Prototype under active development ahead of the Aug 8, 2026 submission. No tagged release
yet — this section covers everything since the project started.

### Added
- The site now says how old its data is: a "Data vintage" note on /methodology and a
  footer bar on the dashboard show the last pipeline-refresh date alongside the dry-season
  imagery window it was computed from (surfaced from the pipeline run log via
  /api/v1/meta; issue #124). The pipeline run log now records that window and is mirrored
  to `frontend/public/`, so the note updates itself on every refresh.
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
