# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Prototype under active development ahead of the Aug 8, 2026 submission. No tagged release
yet — this section covers everything since the project started.

### Added
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

### Fixed
- Dashboard sidebar scroll, fullscreen popup theming in dark mode, ward search matching
  by locality name as well as ward code.
