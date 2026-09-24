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

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import ee
import _gee_cache
import _provenance

from _dry_season import most_recent_complete_dry_season
from _gee_auth import init_ee, resolve_project
from _city import load_city

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Resolved from the city config rather than spelled literally, so this stage
# reads the grid stage 01 actually wrote. These were hardcoded to
# data/grid_1km*.geojson, which meant a non-default city read Mumbai's grid and
# wrote its results over Mumbai's outputs, and a non-default resolution was
# invisible in the filename entirely. See CityConfig.grid_path (issue #96).
_CITY = load_city()
GRID_PATH = _CITY.grid_path()
OUT_PATH = _CITY.grid_path("_gee")

GEE_PROJECT = resolve_project()

# How far back the NDVI-change baseline sits, in years. Roughly a decade gives a
# green-cover trend long enough to be a real signal rather than year-to-year
# weather.
BASELINE_GAP_YEARS = 9

# The dry-season window logic lives in _dry_season.py, shared with
# run_pipeline.py so the run log records the same window this stage composites.
CURR_START, CURR_END = most_recent_complete_dry_season()
# Older dry-season baseline for the F6 green-cover-change layer, the same months
# a fixed number of years earlier so the two composites are comparable.
_prev_end_year = int(CURR_END[:4]) - BASELINE_GAP_YEARS
PREV_START, PREV_END = most_recent_complete_dry_season(date(_prev_end_year, 6, 1))

MAX_CLOUD = 20
SR_SCALE, SR_OFFSET = 2.75e-05, -0.2
ST_SCALE, ST_OFFSET = 0.00341802, 149.0
ZONAL_SCALE = 30  # Landsat native resolution
WORLDCOVER_SCALE = 10
WORLDCOVER_BUILTUP_CLASS = 50

# Below this many cloud-free observations, a cell's LST rests on too little
# imagery to trust and is flagged (issue #94).
#
# Three is a floor, not a comfort level. A dry-season window is about four
# months of Landsat 8 and 9, so a clear cell sees roughly eight to sixteen
# passes; a cell down at two is persistently clouded or persistently masked,
# and a median over two observations is barely a median. Stage 14 already uses
# four scenes as its per-year floor for fitting a trend, which is the same
# judgement applied to a longer window.
MIN_CLEAR_OBS = 3


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Refetch from Earth Engine even when a cached result matches (issue #93).",
    )
    return parser.parse_args()


def main(args: argparse.Namespace) -> int:
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

    # How much usable imagery each pixel actually had (issue #94).
    #
    # mask_l2_clouds has already masked cloud and shadow, so count() over the
    # collection is the number of observations that survived per pixel. Reduced
    # per cell below, it becomes the mean clear observations backing that
    # cell's LST.
    #
    # Without this a cell composited from two clear scenes and one composited
    # from twelve carry identical weight in the index, and nothing anywhere
    # records the difference. Cloud contamination biases LST, and this is the
    # only measure of the exposure.
    clear_obs = curr.select("ST_B10").count().rename("lst_clear_obs")

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

    stack = lst_c.addBands(ndvi_curr).addBands(ndvi_prev).addBands(impervious_pct).addBands(clear_obs)

    zonal = stack.reduceRegions(
        collection=grid_fc,
        reducer=ee.Reducer.mean(),
        scale=ZONAL_SCALE,
    )

    # Everything that can change the answer goes into the key (issue #93).
    # Miss one and a hit would serve numbers computed for a different
    # question, which is worse than no cache at all.
    with open(GRID_PATH, encoding="utf-8") as f:
        _grid_for_key = json.load(f)
    key = _gee_cache.cache_key(
        bbox=region.bounds().getInfo()["coordinates"],
        current_window=[CURR_START, CURR_END],
        previous_window=[PREV_START, PREV_END],
        collections=[
            "LANDSAT/LC08/C02/T1_L2",
            "LANDSAT/LC09/C02/T1_L2",
            "ESA/WorldCover/v200",
        ],
        scale=ZONAL_SCALE,
        max_cloud=MAX_CLOUD,
        grid=_gee_cache.grid_fingerprint(_grid_for_key["features"]),
    )

    result = None if args.no_cache else _gee_cache.load(key)
    if result is not None:
        print(f"[ok] reusing cached zonal statistics for this window ({key[:12]})")
    else:
        print("[..] running reduceRegions over all cells (may take a minute)")
        result = zonal.getInfo()
        _gee_cache.store(
            key,
            result,
            describe={
                "window": f"{CURR_START}..{CURR_END}",
                "cells": n_cells,
                "scenes": n_curr,
            },
        )
        print(f"[ok] cached zonal statistics ({key[:12]})")

    props_by_id = {}
    for feat in result["features"]:
        p = feat["properties"]
        props_by_id[p["grid_id"]] = {
            "LST_C": p.get("LST_C"),
            "NDVI": p.get("NDVI"),
            "NDVI_prev": p.get("NDVI_prev"),
            "impervious_pct": p.get("impervious_pct"),
            "lst_clear_obs": p.get("lst_clear_obs"),
        }

    with open(GRID_PATH, encoding="utf-8") as f:
        grid_gj = json.load(f)
    matched = 0
    sparse = 0
    for feat in grid_gj["features"]:
        gid = feat["properties"]["grid_id"]
        vals = props_by_id.get(gid, {})
        feat["properties"].update(vals)

        # Flagged rather than dropped (issue #94). Dropping would change the
        # cell count between runs, which every downstream stage, the published
        # dataset and the quality gate's tolerance all treat as a stable
        # property of the grid. A flag lets a consumer exclude these cells
        # without the pipeline silently reshaping itself.
        obs = vals.get("lst_clear_obs")
        is_sparse = obs is not None and obs < MIN_CLEAR_OBS
        feat["properties"]["lst_obs_sparse"] = is_sparse
        if is_sparse:
            sparse += 1

        if vals.get("LST_C") is not None:
            matched += 1

    OUT_PATH.write_text(json.dumps(grid_gj), encoding="utf-8")
    print(f"[ok] wrote {len(grid_gj['features'])} cells ({matched} with LST) -> {OUT_PATH}")

    observed = [v["lst_clear_obs"] for v in props_by_id.values() if v.get("lst_clear_obs") is not None]
    if observed:
        observed.sort()
        print(f"[ok] clear observations per cell: min {observed[0]:.1f}, "
              f"median {observed[len(observed) // 2]:.1f}, max {observed[-1]:.1f}")
    if sparse:
        print(f"[WARN] {sparse} cell(s) below {MIN_CLEAR_OBS} clear observations, "
              "flagged lst_obs_sparse. Their LST rests on very little imagery.")
    _provenance.record(
        "02",
        collections=[
            "LANDSAT/LC08/C02/T1_L2",
            "LANDSAT/LC09/C02/T1_L2",
            "ESA/WorldCover/v200",
        ],
        composite_window={"start": CURR_START, "end": CURR_END},
        previous_window={"start": PREV_START, "end": PREV_END},
        scenes_current_window=n_curr,
        scenes_previous_window=n_prev,
        cells_in=n_cells,
        cells_out=len(grid_gj["features"]),
        cells_with_lst=matched,
        gee_project=GEE_PROJECT,
    )

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
    sys.exit(main(parse_args()))
