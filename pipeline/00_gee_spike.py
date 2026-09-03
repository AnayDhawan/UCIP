"""Stage 00 — Earth Engine connectivity check. Not part of a data refresh.

What it does:
    Pulls a dry-season LST and NDVI composite over one small fixed test area in
    central Mumbai (roughly the Dadar/Sion belt), prints region statistics with
    sanity checks, and saves preview thumbnails. It writes nothing any later
    stage reads.

    Originally the go/no-go gate: if this ran clean end to end, the live-Earth-
    Engine pipeline was viable, and if it fought back for a day the plan was to
    pivot to pre-downloaded rasters. It cleared on 2026-07-12 and the pivot was
    never needed. It stays in the repo as a credentials smoke test, which is
    the fastest way to tell a broken Earth Engine auth from a broken stage.

    Excluded from a plain `python run_pipeline.py` for that reason; pass
    --include-spike to run it anyway.

Inputs:
    Google Earth Engine     Landsat 8/9 C2 L2 over TEST_BBOX (needs auth)

Outputs:
    pipeline/spike_lst.png, pipeline/spike_ndvi.png     thumbnails, not committed
    stdout                                              region statistics

Notes:
    The mean LST this prints is for the small test bbox, NOT for Mumbai. The
    city-wide figure across all cells comes from stage 05 and is roughly 1.2 C
    lower. Quoting this number as a city figure has caused a real error in a
    deck before.

Prereqs:
    1. An approved Earth Engine account (code.earthengine.google.com/register)
    2. `earthengine authenticate` run once in this venv, or a service account
       configured per _gee_auth.py
    3. GEE_PROJECT set below or via env var

Run:
    .venv\\Scripts\\activate
    python 00_gee_spike.py
"""

import sys
import urllib.request

import ee

from _gee_auth import init_ee, resolve_project

# ---------------------------------------------------------------- config ----
GEE_PROJECT = resolve_project()

# Small test bbox: central Mumbai (roughly Dadar/Sion belt). One ward-sized area.
TEST_BBOX = [72.83, 19.00, 72.92, 19.08]  # [west, south, east, north]

# Dry season composite window (monsoon imagery is unusable for LST).
DRY_START = "2025-11-01"
DRY_END = "2026-02-28"

MAX_CLOUD = 20  # % scene cloud cover filter

# Landsat Collection 2 Level-2 scale factors (USGS documented).
SR_SCALE, SR_OFFSET = 2.75e-05, -0.2          # surface reflectance bands
ST_SCALE, ST_OFFSET = 0.00341802, 149.0       # surface temperature band (Kelvin)


def mask_l2_clouds(img: ee.Image) -> ee.Image:
    """Mask clouds + cloud shadow via QA_PIXEL bits (3 = cloud, 4 = shadow)."""
    qa = img.select("QA_PIXEL")
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.updateMask(mask)


def main() -> int:
    init_ee(GEE_PROJECT)
    print(f"[ok] Earth Engine initialized (project={GEE_PROJECT})")

    region = ee.Geometry.Rectangle(TEST_BBOX)

    landsat = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterBounds(region)
        .filterDate(DRY_START, DRY_END)
        .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
        .map(mask_l2_clouds)
    )

    n_scenes = landsat.size().getInfo()
    print(f"[ok] {n_scenes} Landsat 8/9 scenes in dry-season window {DRY_START}..{DRY_END}")
    if n_scenes == 0:
        print("[FAIL] No scenes found. Widen the date window or relax MAX_CLOUD.")
        return 1

    composite = landsat.median()

    # LST in deg C from ST_B10.
    lst_c = composite.select("ST_B10").multiply(ST_SCALE).add(ST_OFFSET).subtract(273.15).rename("LST_C")

    # NDVI from scaled SR bands (B5 = NIR, B4 = red).
    nir = composite.select("SR_B5").multiply(SR_SCALE).add(SR_OFFSET)
    red = composite.select("SR_B4").multiply(SR_SCALE).add(SR_OFFSET)
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")

    stats = (
        lst_c.addBands(ndvi)
        .reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
            geometry=region,
            scale=100,
            maxPixels=1e9,
        )
        .getInfo()
    )

    lst_mean = stats.get("LST_C_mean")
    ndvi_mean = stats.get("NDVI_mean")
    print("\n--- region statistics (central Mumbai test bbox) ---")
    for k in sorted(stats):
        print(f"  {k:14s} = {stats[k]:.3f}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    if lst_mean is None or not (20.0 <= lst_mean <= 45.0):
        print(f"[WARN] mean LST {lst_mean} outside plausible urban dry-season range 20-45 C")
        ok = False
    if ndvi_mean is None or not (-1.0 <= ndvi_mean <= 1.0) or not (0.0 <= ndvi_mean <= 0.6):
        print(f"[WARN] mean NDVI {ndvi_mean} outside plausible urban range ~0-0.6")
        ok = False

    # ------------------------------------------------- preview thumbnails --
    try:
        for name, img, vis in [
            ("spike_lst.png", lst_c, {"min": 25, "max": 45, "palette": ["blue", "yellow", "red"]}),
            ("spike_ndvi.png", ndvi, {"min": 0, "max": 0.6, "palette": ["white", "green"]}),
        ]:
            url = img.getThumbURL({"region": region, "dimensions": 512, **vis})
            urllib.request.urlretrieve(url, name)
            print(f"[ok] wrote {name}")
    except Exception as exc:  # thumbnails are nice-to-have, stats are the gate
        print(f"[warn] thumbnail export failed (non-fatal): {exc}")

    print("\n" + ("GO: GEE pipeline viable." if ok else "CHECK WARNINGS: eyeball thumbnails before calling go/no-go."))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
