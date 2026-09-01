# Pipeline

13 numbered scripts that turn raw Mumbai boundaries + remote-sensing pulls into the GeoJSON / JSON the frontend and Supabase consume. Run sequentially — each stage's output is the next stage's input. No orchestrator yet (see #56); run by hand `00` → `12`.

## Run order

| # | Script | Purpose (1 line) | Reads | Writes |
|---|--------|-------------------|-------|--------|
| 00 | `00_gee_spike.py` | Day-0 GEE go/no-go gate: dry-season LST+NDVI pull for a small central-Mumbai bbox | GEE (live) | stdout + thumbnails (sanity check only) |
| 01 | `01_grid.py` | Build 1 km fishnet grid clipped to 24 BMC wards | `data/bmc_wards.geojson` | `data/grid_1km.geojson` |
| 02 | `02_gee_layers.py` | Pull LST, NDVI (current + 2016-17 baseline), impervious proxy from GEE | GEE + `grid_1km.geojson` | `data/grid_1km_gee.geojson` |
| 03 | `03_vectors.py` | Vector/socio layers: WorldPop density/elderly, Datameet slums, OSM hospitals | GEE (WorldPop) + OSM + `grid_1km_gee.geojson`, `data/slumClusters.geojson` | `data/grid_1km_vectors.geojson` |
| 04 | `04_zonal.py` | Consolidate to tidy per-cell table (canonical indicator set) | `grid_1km_vectors.geojson` | `data/cells.geojson` |
| 05 | `05_hvi.py` | HVI: z-score → PCA (Reid et al. 2009) → 0-100 + per-factor `contrib_*` | `cells.geojson` + `bmc_wards.geojson` | `data/cells_hvi.geojson`, `data/wards_hvi.geojson`, `data/hvi_pca_log.json` |
| 06 | `06_nbs.py` | NBS rule engine + plantability filter (Bastin/Veldman etc.) | `cells_hvi.geojson` + GEE (WorldCover) | `data/cells_nbs.geojson`, `data/nbs_recommendations.json` |
| 07 | `07_load.py` | Upsert to Supabase + write demo-safe snapshots | `cells_nbs.geojson`, `wards_hvi.geojson`, `nbs_recommendations.json` | Supabase (`wards`, `grid_cells`, `nbs_recommendations`, …) + `data/snapshot_*.geojson` |
| 08 | `08_sensitivity.py` | Weight perturbation (±20% one-at-a-time) + Kendall τ stability chart | `cells.geojson`, `hvi_pca_log.json` | `data/sensitivity.json`, `data/sensitivity_chart.png` |
| 09 | `09_ndvi_change.py` | Classify per-cell NDVI delta → `gained/stable/lost` (thr ±0.05) | `cells_hvi.geojson` | `data/cells_ndvi_change.geojson` |
| 10 | `10_ward_profile.py` | Roll cell indicators to ward profiles (dialog copy context) | `cells_hvi.geojson`, `wards_hvi.geojson`, `bmc_wards.geojson` | `data/ward_profiles.json` |
| 11 | `11_hero_city.py` | Project + simplify wards for 3D hero (unit-space `[-1,1]`) | `bmc_wards.geojson`, `wards_hvi.geojson` | `data/hero_city.json` |
| 12 | `12_hero_region.py` | Regional coastline context around Mumbai (Natural Earth) | `hero_city.json` (shared `space`) + Natural Earth cache | `data/hero_region.json` |

Where the pipeline hands off:
- `data/` snapshots → what the frontend currently reads from `frontend/public/` (copy of `data/` snapshots). After #53, live reads come from Supabase instead.
- Supabase tables → live source for the dashboard once `07_load` has run against a migrated DB (`supabase/migrations/0001_init.sql`).

## How to run end-to-end (local)

```bash
# 1. Python env (3.11+)
python -m venv .venv
.venv\Scripts\activate        # Windows — or source .venv/bin/activate on macOS/Linux
pip install -r pipeline/requirements.txt

# 2. Credentials — see .env.example
#    Copy to .env.local in repo root (07_load.py loads .env.local):
#      NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY  (for 07_load.py)
#      GEE_PROJECT=ucip-mumbai  (also settable as env var; must have run `earthengine authenticate` once)
cp .env.example .env.local          # then fill values
# GEE auth (once per machine):
earthengine authenticate

# 3. Run sequentially
python pipeline/00_gee_spike.py   # optional spike/gate — skip if GEE already proven
python pipeline/01_grid.py
python pipeline/02_gee_layers.py
python pipeline/03_vectors.py
python pipeline/04_zonal.py
python pipeline/05_hvi.py
python pipeline/06_nbs.py
python pipeline/07_load.py        # writes snapshots even if Supabase is not configured
python pipeline/08_sensitivity.py
python pipeline/09_ndvi_change.py
python pipeline/10_ward_profile.py
python pipeline/11_hero_city.py
python pipeline/12_hero_region.py

# 4. Frontend picks up fresh snapshots (copied or symlinked to frontend/public/)
#    e.g. copy data/wards_hvi.geojson → frontend/public/wards_hvi.geojson etc.
```

`07_load.py` is best-effort on Supabase: if `0001_init.sql` hasn't been applied, it logs per-table failures and still writes snapshots — the judged demo survives a dead DB by design.

## Env vars / credentials

| Var | Where used | Required? |
|-----|------------|-----------|
| `GEE_PROJECT` | `00`, `02`, `03`, `06` | Yes for any GEE pull |
| `NEXT_PUBLIC_SUPABASE_URL` | `07_load.py` (loads `.env.local`) | Only for live DB upsert |
| `SUPABASE_SERVICE_ROLE_KEY` | `07_load.py` (loads `.env.local`) | Only for live DB upsert |

Source of truth for env names: `.env.example` at repo root.

## Notes

- Sequential by construction — later stages assume earlier outputs exist. The planned orchestrator (#56) is one command around this same order.
- GEE stages use dry-season windows validated in `00_gee_spike.py` (`2025-11-01` → `2026-02-28` current, `2016-11-01` → `2017-02-28` baseline).
- This doc is the bird's-eye map; per-script docstrings are the per-stage detail (see #19).
