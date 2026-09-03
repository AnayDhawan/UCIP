"""Stage 02 — Pull the satellite layers from Google Earth Engine onto the grid.

What it does:
    Builds three cloud-masked dry-season composites from Landsat 8/9 Collection 2
    Level 2 and ESA WorldCover, then reduces each one over the grid cells so
    every cell gains its own measured value. Reduction happens server-side in
    Earth Engine (reduceRegions) rather than by downloading rasters, so nothing
    large ever lands on disk.

    Three layers come out of this stage:
      - LST_C, dry-season median land surface temperature from ST_B10.
      - NDVI, dry-season median vegetation index for the current window.
      - NDVI_prev, the same index over a window roughly nine years earlier,
        which is what stage 09 differences to get green-cover change.
      - impervious_pct, built-up share from WorldCover class 50.

    Monsoon imagery is excluded on purpose: cloud cover makes wet-season LST
    unusable, so both windows are dry-season only and therefore comparable.

Inputs:
    ../data/grid_1km.geojson    the grid from stage 01
    Google Earth Engine         Landsat 8/9 C2 L2, ESA WorldCover (needs auth)

Outputs:
    ../data/grid_1km_gee.geojson    the grid plus LST_C, NDVI, NDVI_prev,
                                    impervious_pct per cell

Notes:
    The compositing recipe (cloud mask, scale and offset constants, dry-season
    window) is the one validated end to end by 00_gee_spike.py before the build
    started. Changing it here changes every published figure downstream.

See docs/methodology.md sections 2 and 7 for the layer definitions.

Run:
    .venv\\Scripts\\activate
    python 02_gee_layers.py
"""

import json
import sys
from pathlib import Path

import ee

from _gee_auth import init_ee, resolve_project

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRID_PATH = DATA_DIR / "grid_1km.geojson"
OUT_PATH = DATA_DIR / "grid_1km_gee.geojson"

GEE_PROJECT = resolve_project()

# Same dry-season window validated by the Day-0 spike (00_gee_spike.py).
CURR_START, CURR_END = "2025-11-01", "2026-02-28"
# Older dry-season baseline for the F6 NDVI-change layer (~9yr gap).
PREV_START, PREV_END = "2016-11-01", "2017-02-28"

MAX_CLOUD = 20
SR_SCALE, SR_OFFSET = 2.75e-05, -0.2
ST_SCALE, ST_OFFSET = 0.00341802, 149.0
ZONAL_SCALE = 30  # Landsat native resolution
WORLDCOVER_SCALE = 10
WORLDCOVER_BUILTUP_CLASS = 50


def mask_l2_clouds(img: ee.Image) -> ee.Image:
    qa = img.select("QA_PIXEL")
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.updateMask(mask)


def landsat_collection(start: str, end: str, region: ee.Geometry) -> ee.ImageCollection:
    return (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
        .map(mask_l2_clouds)
    )


def ndvi_from_composite(composite: ee.Image) -> ee.Image:
    nir = composite.select("SR_B5").multiply(SR_SCALE).add(SR_OFFSET)
    red = composite.select("SR_B4").multiply(SR_SCALE).add(SR_OFFSET)
    return nir.subtract(red).divide(nir.add(red)).rename("NDVI")


def load_grid_fc(path: Path) -> ee.FeatureCollection:
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)
    features = []
    for feat in gj["features"]:
        props = {"grid_id": feat["properties"]["grid_id"]}
        features.append(ee.Feature(ee.Geometry(feat["geometry"]), props))
    return ee.FeatureCollection(features)


def main() -> int:
    if not GRID_PATH.exists():
        print(f"[FAIL] {GRID_PATH} not found — run 01_grid.py first.")
        return 1

    init_ee(GEE_PROJECT)
    print(f"[ok] Earth Engine initialized (project={GEE_PROJECT})")

    grid_fc = load_grid_fc(GRID_PATH)
    n_cells = grid_fc.size().getInfo()
    print(f"[ok] loaded {n_cells} grid cells")

    region = grid_fc.geometry().bounds()

    curr = landsat_collection(CURR_START, CURR_END, region)
    n_curr = curr.size().getInfo()
    print(f"[ok] {n_curr} Landsat scenes in current window {CURR_START}..{CURR_END}")
    if n_curr == 0:
        print("[FAIL] no current-window scenes found.")
        return 1
    curr_composite = curr.median()
    lst_c = curr_composite.select("ST_B10").multiply(ST_SCALE).add(ST_OFFSET).subtract(273.15).rename("LST_C")
    ndvi_curr = ndvi_from_composite(curr_composite).rename("NDVI")

    prev = landsat_collection(PREV_START, PREV_END, region)
    n_prev = prev.size().getInfo()
    print(f"[ok] {n_prev} Landsat scenes in previous window {PREV_START}..{PREV_END}")
    if n_prev == 0:
        print("[WARN] no previous-window scenes — NDVI_prev will be null, F6 change layer degrades gracefully.")
        ndvi_prev = ee.Image.constant(0).rename("NDVI_prev").updateMask(ee.Image.constant(0))
    else:
        ndvi_prev = ndvi_from_composite(prev.median()).rename("NDVI_prev")

    worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()
    impervious_pct = (
        worldcover.eq(WORLDCOVER_BUILTUP_CLASS)
        .rename("impervious_frac")
        .multiply(100)
        .rename("impervious_pct")
    )

    stack = lst_c.addBands(ndvi_curr).addBands(ndvi_prev).addBands(impervious_pct)

    zonal = stack.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean(),
        scale=ZONAL_SCALE,
    )

    print("[..] running reduceRegions over all cells (may take a minute)")
    result = zonal.getInfo()

    props_by_id = {}
    for feat in result["features"]:
        p = feat["properties"]
        props_by_id[p["grid_id"]] = {
            "LST_C": p.get("LST_C"),
            "NDVI": p.get("NDVI"),
            "NDVI_prev": p.get("NDVI_prev"),
            "impervious_pct": p.get("impervious_pct"),
        }

    with open(GRID_PATH, encoding="utf-8") as f:
        grid_gj = json.load(f)
    matched = 0
    for feat in grid_gj["features"]:
        gid = feat["properties"]["grid_id"]
        vals = props_by_id.get(gid, {})
        feat["properties"].update(vals)
        if vals.get("LST_C") is not None:
            matched += 1

    OUT_PATH.write_text(json.dumps(grid_gj), encoding="utf-8")
    print(f"[ok] wrote {len(grid_gj['features'])} cells ({matched} with LST) -> {OUT_PATH}")

    # ------------------------------------------------------- sanity checks --
    lst_vals = [f["properties"]["LST_C"] for f in grid_gj["features"] if f["properties"].get("LST_C") is not None]
    ndvi_vals = [f["properties"]["NDVI"] for f in grid_gj["features"] if f["properties"].get("NDVI") is not None]
    ok = True
    if not lst_vals or not (20.0 <= sum(lst_vals) / len(lst_vals) <= 45.0):
        print(f"[WARN] mean LST {sum(lst_vals)/len(lst_vals) if lst_vals else None} outside plausible range")
        ok = False
    if not ndvi_vals or not (0.0 <= sum(ndvi_vals) / len(ndvi_vals) <= 0.6):
        print(f"[WARN] mean NDVI {sum(ndvi_vals)/len(ndvi_vals) if ndvi_vals else None} outside plausible range")
        ok = False
    if matched < 0.9 * len(grid_gj["features"]):
        print(f"[WARN] only {matched}/{len(grid_gj['features'])} cells got LST values")
        ok = False
    print(f"\n{'GO' if ok else 'CHECK WARNINGS'}: mean LST={sum(lst_vals)/len(lst_vals):.2f}C, mean NDVI={sum(ndvi_vals)/len(ndvi_vals):.3f}" if lst_vals and ndvi_vals else "\nFAIL: no valid stats")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
