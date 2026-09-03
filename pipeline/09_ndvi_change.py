"""Stage 09 — Classify green-cover change per cell as gained, stable, or lost.

What it does:
    Differences the two NDVI composites stage 02 already computed for every cell
    (current dry season against a dry-season baseline roughly nine years
    earlier) and classifies the delta into gained, stable, or lost. That becomes
    the third map layer on the dashboard, overlaid on the same cells as the
    index.

    Purely a classification step: no new satellite data is fetched here, because
    both NDVI values arrive from stage 02. Comparing dry season to dry season is
    what makes the difference meaningful rather than seasonal.

Inputs:
    ../data/cells_hvi.geojson       cells carrying NDVI and NDVI_prev

Outputs:
    ../data/cells_ndvi_change.geojson        cells plus delta and class
    frontend/public/cells_ndvi_change.geojson

Threshold: methodology.md specifies the delta-then-classify logic but not the exact
cutoff, so this documents the choice made here: +/-0.05 NDVI delta, consistent in
spirit with the +/-20% perturbation tolerance already used in 08_sensitivity.py as
"the size of change we'd actually trust as real signal, not noise" for this dataset.

Run:
    .venv\\Scripts\\activate
    python 09_ndvi_change.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from _publish import publish

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

    # ------------------------------------------------------- sanity checks --
    # Runs BEFORE the frontend/public copy below, on purpose -- see 05_hvi.py's
    # matching comment.
    counts = out["change_class"].value_counts().to_dict()
    print(f"\nclass counts: {counts}")
    ok = counts.get("unknown", 0) < 0.1 * len(out)

    if ok:
        publish(OUT_PATH, OUT_PUBLIC_PATH)
    else:
        print(f"[WARN] sanity check failed -- NOT copying to {OUT_PUBLIC_PATH}; "
              "the live site keeps serving its previous cells_ndvi_change.geojson")

    print("GO" if ok else "CHECK WARNINGS: too many 'unknown' cells")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
