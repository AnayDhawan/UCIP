"""F6 — Green-cover change layer: per-cell NDVI delta classified gained/stable/lost.

Planned (methodology.md §7): NDVI at two dates -> per-cell delta -> gained/stable/lost,
overlaid with HVI.

`NDVI` (current dry season) and `NDVI_prev` (older dry-season baseline) are already
computed per cell in 02_gee_layers.py; this script is just the classification step.

Threshold: methodology.md specifies the delta-then-classify logic but not the exact
cutoff, so this documents the choice made here: +/-0.05 NDVI delta, consistent in
spirit with the +/-20% perturbation tolerance already used in 08_sensitivity.py as
"the size of change we'd actually trust as real signal, not noise" for this dataset.

Run:
    .venv\\Scripts\\activate
    python 09_ndvi_change.py
"""

import shutil
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IN_PATH = DATA_DIR / "cells_hvi.geojson"
OUT_PATH = DATA_DIR / "cells_ndvi_change.geojson"
# WardChoropleth.tsx's green-cover-change layer fetches this straight from the
# browser, so it needs a frontend/public/ copy on every refresh, same as
# 10_ward_profile.py/11_hero_city.py/12_hero_region.py already do for theirs.
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "cells_ndvi_change.geojson"

GAIN_THRESHOLD = 0.05
LOSS_THRESHOLD = -0.05


def classify(delta: float) -> str:
    if delta > GAIN_THRESHOLD:
        return "gained"
    if delta < LOSS_THRESHOLD:
        return "lost"
    return "stable"


def main() -> int:
    if not IN_PATH.exists():
        print(f"[FAIL] {IN_PATH} not found — run 05_hvi.py first.")
        return 1

    gdf = gpd.read_file(IN_PATH)
    print(f"[ok] loaded {len(gdf)} cells")

    missing_prev = gdf["NDVI_prev"].isna().sum()
    if missing_prev:
        print(f"[WARN] {missing_prev}/{len(gdf)} cells missing NDVI_prev — will be classified 'unknown'")

    deltas, classes = [], []
    for _, row in gdf.iterrows():
        if pd.isna(row["NDVI_prev"]) or pd.isna(row["NDVI"]):
            deltas.append(None)
            classes.append("unknown")
        else:
            delta = row["NDVI"] - row["NDVI_prev"]
            deltas.append(delta)
            classes.append(classify(delta))

    gdf["ndvi_delta"] = deltas
    gdf["change_class"] = classes

    out_cols = ["grid_id", "ward_id", "NDVI", "NDVI_prev", "ndvi_delta", "change_class", "HVI", "geometry"]
    out = gdf[out_cols]
    out.to_file(OUT_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(out)} cells with NDVI-change classification -> {OUT_PATH}")

    OUT_PUBLIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT_PATH, OUT_PUBLIC_PATH)
    print(f"[ok] copied -> {OUT_PUBLIC_PATH}")

    # ------------------------------------------------------- sanity checks --
    counts = out["change_class"].value_counts().to_dict()
    print(f"\nclass counts: {counts}")
    ok = counts.get("unknown", 0) < 0.1 * len(out)
    print("GO" if ok else "CHECK WARNINGS: too many 'unknown' cells")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
