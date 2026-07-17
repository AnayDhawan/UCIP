"""M2 — Zonal statistics: rasters + vectors -> one row per grid cell.

Planned (sprint Aug 2):
- Aggregate every layer (LST, NDVI, NDVI_prev, pop, elderly, slum, hospital_dist,
  impervious) to grid cells (mean per cell).
- Output a tidy cells table (GeoDataFrame) feeding 05_hvi.py.

02_gee_layers.py and 03_vectors.py already write their columns directly onto the
grid (one row per cell each), so this step is the consolidation + tidy-schema pass:
select the canonical column set, drop intermediate ones, enforce dtypes, drop any
cell missing a required indicator (would break z-standardization in 05_hvi.py).

Run:
    .venv\\Scripts\\activate
    python 04_zonal.py
"""

import sys
from pathlib import Path

import geopandas as gpd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IN_PATH = DATA_DIR / "grid_1km_vectors.geojson"
OUT_PATH = DATA_DIR / "cells.geojson"

# Canonical indicator set consumed by 05_hvi.py (methodology.md §3).
INDICATOR_COLS = [
    "LST_C", "NDVI", "pop_density_km2", "elderly_pct",
    "slum_pct", "hospital_dist_m", "impervious_pct",
]
KEEP_COLS = ["grid_id", "ward_id", "ward_gid", "NDVI_prev", "geometry"] + INDICATOR_COLS


def main() -> int:
    if not IN_PATH.exists():
        print(f"[FAIL] {IN_PATH} not found — run 02_gee_layers.py and 03_vectors.py first.")
        return 1

    gdf = gpd.read_file(IN_PATH)
    print(f"[ok] loaded {len(gdf)} cells with columns: {list(gdf.columns)}")

    missing_cols = [c for c in KEEP_COLS if c not in gdf.columns]
    if missing_cols:
        print(f"[FAIL] missing expected columns: {missing_cols}")
        return 1

    tidy = gdf[KEEP_COLS].copy()

    before = len(tidy)
    tidy = tidy.dropna(subset=INDICATOR_COLS)
    dropped = before - len(tidy)
    if dropped:
        print(f"[WARN] dropped {dropped}/{before} cells with a missing indicator value")

    tidy = tidy.reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_file(OUT_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(tidy)} tidy cells -> {OUT_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    if len(tidy) < 0.85 * before:
        print(f"[WARN] lost >15% of cells to missing data ({len(tidy)}/{before} kept)")
        ok = False
    if tidy["ward_id"].nunique() < 20:
        print(f"[WARN] only {tidy['ward_id'].nunique()} wards represented after cleaning")
        ok = False
    print("\nGO" if ok else "\nCHECK WARNINGS")
    print(tidy[INDICATOR_COLS].describe().to_string())
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
