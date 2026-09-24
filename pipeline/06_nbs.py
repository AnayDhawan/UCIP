"""Stage 06 — Recommend interventions, gated by an ecological plantability filter.

What it does:
    Turns each ward's index into a concrete, cited recommendation. Runs a
    rule engine over the scored cells where every fired rule carries both a
    plain-language rationale and the paper backing it:

        HVI high + canopy low + plantable      -> native trees, green corridors  [Bastin]
        HVI high + canopy low + NOT plantable  -> cool roofs, reflective paving,
                                                  cooling centres                [Veldman]
        impervious high + flood-prone          -> rain gardens, WSUD
        density high + open space low          -> pocket parks
        elderly high + hospital access far     -> cooling centres, prioritised

    The plantability filter is the part that makes this more than a lookup
    table. A cell qualifies for tree planting only where restoration literature
    supports it: Bastin 2019 for where trees can go, constrained by Veldman 2019
    on not afforesting native grassland and savanna. Where a hot ward fails that
    test it is refused trees and assigned non-tree cooling instead, which is the
    honest answer rather than the popular one.

Inputs:
    ../data/cells_hvi.geojson   scored cells from stage 05
    Google Earth Engine         ESA WorldCover land cover, water distance

Outputs:
    ../data/cells_nbs.geojson           cells plus plantable flag and land cover
    ../data/nbs_recommendations.json    per-ward recommendations, ranked
    frontend/public/ copies of both     published for the site

Threshold notes (documented here since methodology.md keeps them at the outline level):
- "high"/"low" cutoffs use the 75th/25th percentile of that indicator across cells
  in THIS run, not fixed absolute values — several indicators (e.g. elderly_pct)
  have a narrow observed range where an absolute cutoff would be meaningless.
- "flood-prone" has no dedicated hydrology layer in P0; proxied as
  distance-to-nearest-WorldCover-water/wetland < 500m (stated limitation).
- "plantable" = not water/wetland/mangrove/built-up AND not native grassland
  (WorldCover class 30) AND impervious_pct below the 75th percentile (physical
  room to plant).

Run:
    .venv\\Scripts\\activate
    python 06_nbs.py
"""

import json
import sys
from pathlib import Path

import ee
import geopandas as gpd
import _provenance

from _city import load_city
import pandas as pd

from _gee_auth import init_ee, resolve_project
from _publish import publish

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Output paths come from the city config (issue #96). They were literal
# DATA_DIR paths, so this stage wrote to the default city's directory whatever
# city or resolution it was actually run for. A 500 m run reached stage 05 with
# 500 m inputs and then published 1 km-named output over the committed dataset,
# which is how this was found.
_CITY = load_city()
IN_PATH = _CITY.out("cells_hvi.geojson")
OUT_CELLS_PATH = _CITY.out("cells_nbs.geojson")
OUT_WARD_RECS_PATH = _CITY.out("nbs_recommendations.json")
# Both files are fetched directly by the browser (WardChoropleth.tsx's plantability
# layer reads cells_nbs.geojson; useWardData.ts reads nbs_recommendations.json for the
# dashboard's per-ward NBS list), so both need a frontend/public/ copy on every
# refresh, same as 10_ward_profile.py/11_hero_city.py/12_hero_region.py already do.
OUT_CELLS_PUBLIC_PATH = ROOT / "frontend" / "public" / "cells_nbs.geojson"
OUT_WARD_RECS_PUBLIC_PATH = ROOT / "frontend" / "public" / "nbs_recommendations.json"

GEE_PROJECT = resolve_project()
ZONAL_SCALE = 10  # WorldCover native resolution

# The decision logic lives in _nbs.py, which has no geospatial dependencies, so
# CI can test the part of this stage that would fail silently (issue #98).
from _nbs import (  # noqa: E402
    FLOOD_PRONE_DIST_M,
    WORLDCOVER_GRASSLAND,
    WORLDCOVER_NONPLANTABLE,
    WORLDCOVER_WATER_LIKE,
    fire_rules,
    is_plantable,
)


def load_grid_fc(gdf: gpd.GeoDataFrame) -> ee.FeatureCollection:
    features = [ee.Feature(ee.Geometry(row.geometry.__geo_interface__), {"grid_id": row.grid_id}) for row in gdf.itertuples()]
    return ee.FeatureCollection(features)


def pull_landcover_and_flood_proxy(gdf: gpd.GeoDataFrame) -> dict:
    init_ee(GEE_PROJECT)
    grid_fc = load_grid_fc(gdf)
    worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()

    dominant_class = worldcover.reduceRegions(
        collection=grid_fc, reducer=ee.Reducer.mode(), scale=ZONAL_SCALE
    ).getInfo()

    water_mask = worldcover.remap(list(WORLDCOVER_WATER_LIKE), [1] * len(WORLDCOVER_WATER_LIKE), 0)
    dist_to_water = water_mask.fastDistanceTransform().sqrt().multiply(10).rename("dist_to_water_m")
    flood_proxy = dist_to_water.reduceRegions(
        collection=grid_fc, reducer=ee.Reducer.mean(), scale=ZONAL_SCALE
    ).getInfo()

    landcover_by_id = {f["properties"]["grid_id"]: f["properties"].get("mode") for f in dominant_class["features"]}
    dist_by_id = {f["properties"]["grid_id"]: f["properties"].get("mean") for f in flood_proxy["features"]}
    return landcover_by_id, dist_by_id


def main() -> int:
    if not IN_PATH.exists():
        print(f"[FAIL] {IN_PATH} not found — run 05_hvi.py first.")
        return 1

    gdf = gpd.read_file(IN_PATH)
    print(f"[ok] loaded {len(gdf)} cells")

    print("[..] pulling WorldCover dominant class + water-distance proxy per cell")
    landcover_by_id, dist_by_id = pull_landcover_and_flood_proxy(gdf)
    gdf["worldcover_class"] = gdf["grid_id"].map(landcover_by_id)
    gdf["dist_to_water_m"] = gdf["grid_id"].map(dist_by_id)

    thresholds = {
        "hvi_p75": gdf["HVI"].quantile(0.75),
        "ndvi_p25": gdf["NDVI"].quantile(0.25),
        "density_p75": gdf["pop_density_km2"].quantile(0.75),
        "elderly_p75": gdf["elderly_pct"].quantile(0.75),
        "hospital_p75": gdf["hospital_dist_m"].quantile(0.75),
        "impervious_p75": gdf["impervious_pct"].quantile(0.75),
    }
    print("[ok] thresholds (75th/25th percentile):", {k: round(v, 2) for k, v in thresholds.items()})

    # Routed through _nbs.is_plantable rather than expressed as a vectorised
    # mask here, so the filter that decides whether this tool recommends
    # planting on native grassland is the same code CI tests (issue #98).
    gdf["plantable"] = [
        is_plantable(
            None if pd.isna(wc) else wc,
            None if pd.isna(imp) else imp,
            thresholds["impervious_p75"],
        )
        for wc, imp in zip(gdf["worldcover_class"], gdf["impervious_pct"])
    ]
    n_rejected_grassland = (gdf["worldcover_class"] == WORLDCOVER_GRASSLAND).sum()
    print(f"[ok] {gdf['plantable'].sum()}/{len(gdf)} cells plantable "
          f"({n_rejected_grassland} rejected as native grassland)")

    all_recs = []
    fired_flags = []
    for row in gdf.itertuples():
        recs = fire_rules(row, thresholds)
        fired_flags.append(len(recs) > 0)
        for r in recs:
            all_recs.append({"grid_id": row.grid_id, "ward_id": row.ward_id, **r})

    gdf["nbs_fired"] = fired_flags
    gdf.drop(columns=["geometry"]).to_csv(_CITY.out("cells_nbs_debug.csv"), index=False)
    gdf.to_file(OUT_CELLS_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(gdf)} cells with NBS flags -> {OUT_CELLS_PATH}")
    _provenance.record(
        "06",
        collections=["ESA/WorldCover/v200"],
        cells_in=len(gdf),
        cells_plantable=int(gdf["plantable"].sum()),
        cells_with_recommendation=int(gdf["nbs_fired"].sum()),
        thresholds={k: round(float(v), 4) for k, v in thresholds.items()},
    )

    # ------------------------------------------------- ward-level rollup --
    ward_recs = {}
    for r in all_recs:
        key = (r["ward_id"], r["intervention"])
        if key not in ward_recs:
            ward_recs[key] = {
                "ward_id": r["ward_id"],
                "intervention": r["intervention"],
                "rationale": r["rationale"],
                "citation": r["citation"],
                "priority": r["priority"],
                "cell_count": 0,
            }
        ward_recs[key]["cell_count"] += 1

    ward_recs_list = sorted(ward_recs.values(), key=lambda r: (r["ward_id"], r["priority"]))
    OUT_WARD_RECS_PATH.write_text(json.dumps(ward_recs_list, indent=2), encoding="utf-8")
    print(f"[ok] wrote {len(ward_recs_list)} ward-level recommendation rows -> {OUT_WARD_RECS_PATH}")

    # ------------------------------------------------------- sanity checks --
    # Runs BEFORE the frontend/public copies below, on purpose -- see 05_hvi.py's
    # matching comment. Both files are gated on the same "ok" so a run that fails this
    # check publishes neither a stale-relative-to-cells_nbs recommendations file nor a
    # stale-relative-to-recommendations cells file; they stay a matched pair.
    ok = True
    wards_with_recs = {r["ward_id"] for r in all_recs}
    if len(wards_with_recs) < 15:
        print(f"[WARN] only {len(wards_with_recs)}/24 wards got any recommendation")
        ok = False
    if n_rejected_grassland == 0:
        print("[WARN] plantability filter never rejected a grassland cell — check WorldCover class mapping")
    print(f"\n{len(all_recs)} recommendation rows fired across {len(wards_with_recs)} wards")

    if ok:
        publish(OUT_CELLS_PATH, OUT_CELLS_PUBLIC_PATH)
        publish(OUT_WARD_RECS_PATH, OUT_WARD_RECS_PUBLIC_PATH)
    else:
        print(f"[WARN] sanity check failed -- NOT copying to {OUT_CELLS_PUBLIC_PATH} or "
              f"{OUT_WARD_RECS_PUBLIC_PATH}; the live site keeps serving its previous NBS output")

    print("GO" if ok else "CHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
