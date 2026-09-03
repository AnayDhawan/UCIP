"""M6 — Hero city geometry (feeds the landing page's 3D ward model).

Why this stage exists:
    The landing hero renders Mumbai as an extruded 3D model where each ward's
    height and colour come from its real HVI. That needs the ward boundaries in
    a flat, metric, pre-simplified, browser-sized form. Shipping
    bmc_wards.geojson directly would be ~1 MB of lat/lon rings on the page that
    owns the site's LCP, so this stage projects, simplifies and normalises it
    down to a small JSON of plain vertex rings.

Deliberately additive:
    Reads bmc_wards.geojson + wards_hvi.geojson, writes only hero_city.json.
    Recomputes nothing. HVI and rank are read straight out of wards_hvi.geojson.

Output coordinate space:
    Projected to EPSG:32643 (UTM zone 43N, metres, correct for Mumbai) so the
    city's real shape is preserved, then centred on the city centroid and
    scaled so the longer axis spans exactly 2.0 units, i.e. x and y both land
    in about [-1, 1]. The renderer can treat it as unitless. Ring winding is
    normalised: outer rings counter-clockwise, holes clockwise, which is what
    THREE.Shape expects for correct hole punching.

Run:
    .venv\\Scripts\\activate
    python 11_hero_city.py
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from _city import load_city

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
_CITY = load_city()
IN_BOUNDARIES_PATH = _CITY.boundaries_path
IN_WARDS_PATH = DATA_DIR / "wards_hvi.geojson"
OUT_PATH = DATA_DIR / "hero_city.json"
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "hero_city.json"

# Mumbai sits in UTM zone 43N. Metres, so simplify tolerance is in metres too.
PROJECTED_CRS = _CITY.projected_crs

# Douglas-Peucker tolerance. At hero scale one ward is roughly 100-200 px wide,
# so detail below ~150 m is invisible and only costs bytes.
SIMPLIFY_TOLERANCE_M = 150.0

# Drop islands/slivers smaller than this after simplification. Keeps stray
# specks out of the model without touching any real ward's main body.
MIN_PART_AREA_M2 = 250_000.0

# Longer axis of the normalised model.
TARGET_SPAN = 2.0

COORD_PRECISION = 4
EXPECTED_WARDS = 24


def ring_coords(ring, cx: float, cy: float, scale: float) -> list[list[float]]:
    """Normalise one ring to model space and drop the duplicated closing vertex."""
    pts = [
        [round((x - cx) * scale, COORD_PRECISION), round((y - cy) * scale, COORD_PRECISION)]
        for x, y in ring.coords
    ]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    return pts


def signed_area(pts: list[list[float]]) -> float:
    """Shoelace. Positive means counter-clockwise."""
    total = 0.0
    for i, (x1, y1) in enumerate(pts):
        x2, y2 = pts[(i + 1) % len(pts)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def polygon_parts(geom, cx: float, cy: float, scale: float) -> list[dict]:
    """Flatten a (Multi)Polygon into renderer-ready parts with wound rings."""
    if isinstance(geom, Polygon):
        polys = [geom]
    elif isinstance(geom, MultiPolygon):
        polys = list(geom.geoms)
    else:
        return []

    parts = []
    for poly in polys:
        if poly.is_empty or poly.area < MIN_PART_AREA_M2:
            continue
        outer = ring_coords(poly.exterior, cx, cy, scale)
        if len(outer) < 3:
            continue
        # THREE.Shape wants the outline counter-clockwise and holes clockwise.
        if signed_area(outer) < 0:
            outer.reverse()
        holes = []
        for interior in poly.interiors:
            hole = ring_coords(interior, cx, cy, scale)
            if len(hole) < 3:
                continue
            if signed_area(hole) > 0:
                hole.reverse()
            holes.append(hole)
        parts.append({"outer": outer, "holes": holes})
    return parts


def main() -> int:
    if not IN_BOUNDARIES_PATH.exists():
        print(f"[FAIL] {IN_BOUNDARIES_PATH} not found — run 03_vectors.py first.")
        return 1
    if not IN_WARDS_PATH.exists():
        print(f"[FAIL] {IN_WARDS_PATH} not found — run 05_hvi.py first.")
        return 1

    _id_field = _CITY.ward_id_field
    _w_raw = gpd.read_file(IN_BOUNDARIES_PATH)
    if "gid" not in _w_raw.columns:
        _w_raw = _w_raw.assign(gid=range(1, len(_w_raw) + 1))
    wards = _w_raw[["gid", _id_field, "geometry"]].rename(
        columns={"gid": "ward_gid", "name": "ward_id"}
    )
    print(f"[ok] loaded {len(wards)} ward boundaries")

    scores = gpd.read_file(IN_WARDS_PATH).drop(columns="geometry")
    score_by_ward = {
        str(r["ward_id"]): {
            "hvi": None if r["HVI"] is None else float(r["HVI"]),
            "rank": None if r["rank"] is None else int(r["rank"]),
        }
        for _, r in scores.iterrows()
    }
    print(f"[ok] loaded HVI + rank for {len(score_by_ward)} wards")

    wards = wards.to_crs(PROJECTED_CRS)
    raw_vertices = int(wards.geometry.apply(lambda g: len(g.wkt)).sum())
    wards["geometry"] = wards.geometry.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    print(f"[ok] projected to {PROJECTED_CRS} and simplified at {SIMPLIFY_TOLERANCE_M:.0f} m")

    minx, miny, maxx, maxy = wards.total_bounds
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    span = max(maxx - minx, maxy - miny)
    scale = TARGET_SPAN / span

    features = []
    for row in wards.itertuples():
        parts = polygon_parts(row.geometry, cx, cy, scale)
        if not parts:
            print(f"[WARN] ward {row.ward_id} has no renderable geometry after simplification")
            continue
        score = score_by_ward.get(str(row.ward_id), {"hvi": None, "rank": None})
        features.append(
            {
                "ward_id": str(row.ward_id),
                "ward_gid": int(row.ward_gid),
                "hvi": score["hvi"],
                "rank": score["rank"],
                "parts": parts,
            }
        )

    features.sort(key=lambda f: (f["rank"] is None, f["rank"]))

    payload = {
        "generated_from": "data/bmc_wards.geojson + data/wards_hvi.geojson",
        "projection": PROJECTED_CRS,
        "simplify_tolerance_m": SIMPLIFY_TOLERANCE_M,
        "note": (
            "Model space: centred on the city bounding box, longer axis scaled to "
            f"{TARGET_SPAN}. Outer rings are counter-clockwise, holes clockwise. "
            "Real BMC ward boundaries, not a stylisation."
        ),
        "extent": {
            "width": round((maxx - minx) * scale, COORD_PRECISION),
            "height": round((maxy - miny) * scale, COORD_PRECISION),
        },
        # Published so 12_hero_region.py can place the surrounding coastline in
        # exactly this space without re-deriving it and drifting.
        "space": {
            "origin_easting": cx,
            "origin_northing": cy,
            "scale": scale,
            "metres_per_unit": 1.0 / scale,
        },
        "wards": features,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    OUT_PUBLIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC_PATH.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"[ok] wrote {len(features)} wards -> {OUT_PATH} ({size_kb:.1f} KB)")
    print(f"[ok] copied -> {OUT_PUBLIC_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    if len(features) != EXPECTED_WARDS:
        print(f"[WARN] {len(features)}/{EXPECTED_WARDS} wards in output")
        ok = False

    no_score = [f["ward_id"] for f in features if f["hvi"] is None]
    if no_score:
        print(f"[WARN] wards with no HVI: {no_score}")
        ok = False

    all_pts = [pt for f in features for p in f["parts"] for ring in [p["outer"], *p["holes"]] for pt in ring]
    out_of_range = [pt for pt in all_pts if abs(pt[0]) > TARGET_SPAN or abs(pt[1]) > TARGET_SPAN]
    if out_of_range:
        print(f"[WARN] {len(out_of_range)} vertices outside the normalised range")
        ok = False

    if size_kb > 250:
        print(f"[WARN] {size_kb:.1f} KB is heavy for a landing-page asset, raise SIMPLIFY_TOLERANCE_M")
        ok = False

    n_parts = sum(len(f["parts"]) for f in features)
    print(f"\n[ok] {len(all_pts)} vertices across {n_parts} parts (raw WKT chars before simplify: {raw_vertices})")
    print(f"[ok] model extent {payload['extent']['width']} x {payload['extent']['height']}")
    print("\nMost vulnerable wards (tallest in the model):")
    for f in features[:5]:
        print(f"  {f['rank']:>2}  {f['ward_id']:<5} HVI {f['hvi']:.1f}  {len(f['parts'])} part(s)")

    print("\nGO" if ok else "\nCHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
