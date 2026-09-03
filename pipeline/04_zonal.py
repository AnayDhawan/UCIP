"""Stage 04 — Consolidate the indicator columns into one clean cells table.

What it does:
    Stages 02 and 03 each write their columns straight onto the grid, so the
    zonal aggregation is already done by the time this runs. What is left is the
    tidy-schema pass: select the canonical seven indicators plus the keys and
    geometry, drop the intermediate columns, enforce dtypes, and drop any cell
    missing a required indicator.

    That last step matters more than it sounds. Stage 05 standardises every
    indicator to a z-score, and a single NaN would propagate through the PCA and
    poison the weights for every ward, so an incomplete cell is removed here
    rather than silently carried forward.

Inputs:
    ../data/grid_1km_vectors.geojson    the fully populated grid from stage 03

Outputs:
    ../data/cells.geojson               one tidy row per complete cell

Notes:
    INDICATOR_COLS is the canonical seven-indicator set that the index is defined
    over (methodology.md section 3). Adding an indicator means changing it here
    and in stage 05 together, or the PCA and the published weight table drift
    apart.

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
