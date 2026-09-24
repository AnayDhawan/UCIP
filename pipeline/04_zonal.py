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

import csv
import sys
from pathlib import Path

import geopandas as gpd
import _provenance

from _city import load_city
from _indicators import REQUIRED

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Config-derived, as in stages 02 and 03. cells.geojson keeps its plain name:
# it is the tidy per-cell table every later stage consumes, one per city
# directory, and the resolution that produced it is recorded in the run log
# rather than in the filename.
_CITY = load_city()
IN_PATH = _CITY.grid_path("_vectors")
OUT_PATH = _CITY.out("cells.geojson")

# The indicators every run must have, from _indicators.py. child_pct is optional
# and joined below when a ward-level Census table exists for the city.
INDICATOR_COLS = list(REQUIRED)
KEEP_COLS = ["grid_id", "ward_id", "ward_gid", "NDVI_prev", "geometry"] + INDICATOR_COLS

# Ward-level Census age table, an input rather than an output, so it lives flat
# in data/ beside slumClusters.geojson and does not move with the grid
# resolution. Built by build_census_table.py. Absent for a city that has none.
CENSUS_TABLE = DATA_DIR / f"census2011_ward_age_{_CITY.slug}.csv"

# Carried through when present, but not required. child_source (issue #95)
# says where a cell's age structure came from, and a dataset produced before
# that column existed is still perfectly valid input; demanding it would fail
# a refresh over provenance metadata rather than over data.
OPTIONAL_COLS = ["child_source"]


def attach_child_share(gdf: "gpd.GeoDataFrame") -> bool:
    """Join the Census 0-6 share onto the cells by ward. Returns whether it did.

    Done here rather than in stage 03 on purpose. Stage 03 re-pulls WorldPop and
    OpenStreetMap, both of which can move between runs for reasons unrelated to
    this change, so adding a ward-level join there would have made a rerun
    change unrelated columns. This is a pure lookup against a committed table:
    offline, deterministic, and cheap enough that nobody has to think about it.

    Every ward in the grid must have a row. A missing ward would come out as
    NaN and the dropna below would then silently discard every cell in it, which
    is the kind of failure that looks like a smaller dataset instead of an
    error, so it stops the run instead.

    The share is the ward's, assigned flat to each of its cells. That is honest
    about the source: the Census has no finer resolution than the ward, and
    spreading it smoothly across cells would invent detail it does not have.
    """
    if not CENSUS_TABLE.exists():
        print(f"[note] no Census table at {CENSUS_TABLE.name}; running without child_pct")
        return False

    with CENSUS_TABLE.open(encoding="utf-8", newline="") as handle:
        table = {row["ward_id"]: row for row in csv.DictReader(handle)}

    missing = sorted(set(gdf["ward_id"].unique()) - set(table))
    if missing:
        raise SystemExit(
            f"[FAIL] {CENSUS_TABLE.name} has no row for ward(s) {missing}; "
            "refusing to drop their cells silently. Rebuild it with build_census_table.py."
        )

    gdf["child_pct"] = gdf["ward_id"].map(lambda w: float(table[w]["child_pct"]))
    gdf["child_source"] = gdf["ward_id"].map(lambda w: table[w]["source"])
    print(f"[ok] joined Census child share for {gdf['ward_id'].nunique()} wards "
          f"({gdf['child_pct'].min():.2f}% to {gdf['child_pct'].max():.2f}%)")
    return True


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

    has_child = attach_child_share(gdf)
    indicator_cols = INDICATOR_COLS + (["child_pct"] if has_child else [])

    tidy = gdf[KEEP_COLS + (["child_pct"] if has_child else [])
               + [c for c in OPTIONAL_COLS if c in gdf.columns]].copy()

    before = len(tidy)
    tidy = tidy.dropna(subset=indicator_cols)
    dropped = before - len(tidy)
    if dropped:
        print(f"[WARN] dropped {dropped}/{before} cells with a missing indicator value")

    # A cell with no residents has nobody to be vulnerable, and in Mumbai these
    # are open water and the coastal edge (NDVI below zero). They used to fall
    # out of the index by accident: WorldPop's elderly share is undefined at
    # zero population, so the null-drop above removed them. Now that the share
    # is gone the exclusion is made here, on purpose, so the cell set does not
    # depend on which indicators happen to be defined.
    populated = tidy["pop_density_km2"] > 0
    unpopulated = int((~populated).sum())
    if unpopulated:
        print(f"[note] excluded {unpopulated} cells with zero WorldPop population "
              f"({', '.join(tidy.loc[~populated, 'grid_id'].astype(str))})")
    tidy = tidy[populated]

    tidy = tidy.reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_file(OUT_PATH, driver="GeoJSON")
    print(f"[ok] wrote {len(tidy)} tidy cells -> {OUT_PATH}")
    _provenance.record(
        "04",
        cells_in=len(gdf),
        cells_out=len(tidy),
        columns_out=list(tidy.columns),
    )

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
