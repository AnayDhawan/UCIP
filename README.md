# UCIP — Urban Climate Intelligence Platform

A research-backed decision-support platform that tells a city planner **which Mumbai wards to cool first, why, what intervention to use, and where to spend a fixed budget** — grounded in published climate and ecology literature, not arbitrary weights.

> **Status: pre-sprint.** Build sprint runs **Aug 1–7, 2026** for the TIS × IHFC Delhi "Now or Never Hack 2026" (Domain: The Planet). This repo currently contains scaffolding, environment setup, and planning docs only.

## What it does

1. **Heat Vulnerability Index (HVI)** — grid-level (1 km) choropleth over Mumbai, rolled up to the 24 BMC wards. Weights are literature-derived (PCA per Reid et al. 2009), never arbitrary.
2. **Explainability** — click a ward and see exactly why it scores what it scores: a factor-contribution breakdown of a transparent linear index. No SHAP, by design (nothing black-box to explain).
3. **Nature-Based Solutions engine** — rule-based recommendations (native trees, cool roofs, pocket parks, cooling centres, rain gardens) with an **ecological plantability filter**: trees only where restoration literature supports them (Bastin 2019), non-tree cooling elsewhere (Veldman 2019, Friedlingstein 2019).
4. **Methodology page** — every variable, weight, dataset, assumption, and limitation, with citations.

Demonstrated on Mumbai; the architecture is city-agnostic.

## Structure

```
frontend/   Next.js 15 + TypeScript + Tailwind + Leaflet
pipeline/   Python 3 + Google Earth Engine (data processing, HVI, NBS rules)
supabase/   Postgres + PostGIS schema and migrations
data/       Ward boundaries + committed GeoJSON snapshots (demo-safe fallback)
docs/       Methodology + full citation table
```

## License

MIT — see [LICENSE](LICENSE).
