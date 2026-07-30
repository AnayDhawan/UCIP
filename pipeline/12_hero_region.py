"""M6 — Hero region context (the out-of-focus land around Mumbai).

Why this stage exists:
    The hero model shows Mumbai's 24 wards in full HVI colour, but a city
    floating in a void reads as an abstraction. This adds the real coast around
    it — the mainland, Thane creek, Navi Mumbai, the islands — rendered dim and
    hazed so it stays context and never competes with the scored wards.

Source and licence:
    Natural Earth 1:10m physical vectors (land + ocean), public domain, no
    attribution required though we credit it anyway. Downloaded once and cached
    under data/cache/, so re-runs are offline. Natural Earth at 1:10m is coarse
    close in: it is honest regional coastline, not a survey boundary, which is
    exactly why it renders unhighlighted.

Coordinate space:
    Reads the "space" block written by 11_hero_city.py and reuses its origin and
    scale verbatim, so the coastline and the ward model share one coordinate
    system by construction rather than by coincidence.

Run:
    .venv\\Scripts\\activate
    python 11_hero_city.py    # must run first, writes the shared space block
    python 12_hero_region.py
"""

import json
import sys
import urllib.request
from pathlib import Path

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon, Point

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
IN_CITY_PATH = DATA_DIR / "hero_city.json"
OUT_PATH = DATA_DIR / "hero_region.json"
OUT_PUBLIC_PATH = ROOT / "frontend" / "public" / "hero_region.json"

NE_BASE = "https://naciscdn.org/naturalearth/10m/physical"
NE_LAND = "ne_10m_land.zip"
NE_MINOR_ISLANDS = "ne_10m_minor_islands.zip"

PROJECTED_CRS = "EPSG:32643"

# How far out the context extends, in metres. About 155 km, which reaches the
# Western Ghats inland and well past the harbour, without pulling in so much
# coast that Mumbai stops being the subject.
REGION_RADIUS_M = 155_000.0

# Coarser than the ward model: this geometry is deliberately never in focus.
SIMPLIFY_TOLERANCE_M = 600.0
MIN_PART_AREA_M2 = 4_000_000.0

COORD_PRECISION = 4


def fetch_natural_earth(name: str) -> Path:
    """Download a Natural Earth archive once, then reuse the cached copy."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / name
    if dest.exists():
        print(f"[ok] cached {name}")
        return dest
    url = f"{NE_BASE}/{name}"
    print(f"[..] downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        dest.write_bytes(response.read())
    print(f"[ok] downloaded {name} ({dest.stat().st_size / 1024:.0f} KB)")
    return dest


def ring_coords(ring, cx: float, cy: float, scale: float) -> list[list[float]]:
    pts = [
        [round((x - cx) * scale, COORD_PRECISION), round((y - cy) * scale, COORD_PRECISION)]
        for x, y in ring.coords
    ]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    return pts


def signed_area(pts: list[list[float]]) -> float:
    total = 0.0
    for i, (x1, y1) in enumerate(pts):
        x2, y2 = pts[(i + 1) % len(pts)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def polygon_parts(geom, cx: float, cy: float, scale: float) -> list[dict]:
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
        if signed_area(outer) < 0:
            outer.reverse()
        holes = []
        for interior in poly.interiors:
            if Polygon(interior).area < MIN_PART_AREA_M2:
                continue
            hole = ring_coords(interior, cx, cy, scale)
            if len(hole) < 3:
                continue
            if signed_area(hole) > 0:
                hole.reverse()
            holes.append(hole)
        parts.append({"outer": outer, "holes": holes})
    return parts


def main() -> int:
    if not IN_CITY_PATH.exists():
        print(f"[FAIL] {IN_CITY_PATH} not found — run 11_hero_city.py first.")
        return 1

    city = json.loads(IN_CITY_PATH.read_text(encoding="utf-8"))
    space = city.get("space")
    if not space:
        print("[FAIL] hero_city.json has no 'space' block — re-run 11_hero_city.py.")
        return 1
    cx = float(space["origin_easting"])
    cy = float(space["origin_northing"])
    scale = float(space["scale"])
    print(f"[ok] reusing model space from hero_city.json (1 unit = {space['metres_per_unit'] / 1000:.1f} km)")

    try:
        land_path = fetch_natural_earth(NE_LAND)
        islands_path = fetch_natural_earth(NE_MINOR_ISLANDS)
    except Exception as exc:  # noqa: BLE001 - network failure should be readable, not a traceback
        print(f"[FAIL] could not fetch Natural Earth data: {exc}")
        print("       Connect once to populate data/cache/, then re-runs work offline.")
        return 1

    # Natural Earth ships in WGS84 and covers the whole planet. Reprojecting all
    # of it into a single UTM zone produces garbage far outside zone 43N (the
    # transform is only valid near its central meridian), which then makes the
    # intersection fail. So: cut the region out in lat/lon first, and only
    # project the small surviving subset.
    region_utm = Point(cx, cy).buffer(REGION_RADIUS_M, quad_segs=64)
    region_wgs = gpd.GeoSeries([region_utm], crs=PROJECTED_CRS).to_crs("EPSG:4326").iloc[0]

    layers = []
    for path in (land_path, islands_path):
        gdf = gpd.read_file(f"zip://{path}")
        gdf = gdf.to_crs("EPSG:4326")
        gdf["geometry"] = gdf.geometry.make_valid()
        # A real clip, not a filter: the "land" layer is a handful of continent
        # -sized polygons, and carrying all of Eurasia into the projection step
        # overflows the transform (NaN/Inf vertices ten thousand km off-zone).
        nearby = gpd.clip(gdf, region_wgs)
        nearby = nearby[~nearby.geometry.is_empty]
        layers.append(nearby)
    land = gpd.GeoDataFrame(
        {"geometry": [g for layer in layers for g in layer.geometry]}, crs="EPSG:4326"
    )
    print(f"[ok] clipped {len(land)} land polygons out of the region in lat/lon")

    land = land.to_crs(PROJECTED_CRS)
    land["geometry"] = land.geometry.make_valid()
    clipped = land.clip(region_utm)
    clipped = clipped[~clipped.geometry.is_empty]
    print(f"[ok] clipped to a {REGION_RADIUS_M / 1000:.0f} km disc: {len(clipped)} polygons")

    clipped["geometry"] = clipped.geometry.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True)

    parts: list[dict] = []
    for geom in clipped.geometry:
        parts.extend(polygon_parts(geom, cx, cy, scale))

    payload = {
        "generated_from": "Natural Earth 1:10m physical (land, minor islands)",
        "licence": "Public domain (Natural Earth). No attribution required.",
        "source_url": NE_BASE,
        "projection": PROJECTED_CRS,
        "region_radius_units": round(REGION_RADIUS_M * scale, COORD_PRECISION),
        "simplify_tolerance_m": SIMPLIFY_TOLERANCE_M,
        "note": (
            "Regional coastline context for the hero model, in the same model space as "
            "hero_city.json. Coarse by design: rendered dim and hazed, never highlighted. "
            "Not a survey boundary."
        ),
        "parts": parts,
    }

    OUT_PATH.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    OUT_PUBLIC_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC_PATH.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    size_kb = OUT_PATH.stat().st_size / 1024
    n_pts = sum(len(p["outer"]) + sum(len(h) for h in p["holes"]) for p in parts)
    print(f"[ok] wrote {len(parts)} land parts, {n_pts} vertices -> {OUT_PATH} ({size_kb:.1f} KB)")
    print(f"[ok] copied -> {OUT_PUBLIC_PATH}")

    # ------------------------------------------------------- sanity checks --
    ok = True
    if not parts:
        print("[WARN] no land parts survived clipping — check the region radius")
        ok = False
    if size_kb > 400:
        print(f"[WARN] {size_kb:.1f} KB is heavy for a landing-page asset, raise SIMPLIFY_TOLERANCE_M")
        ok = False

    radius_units = REGION_RADIUS_M * scale
    stray = [
        pt
        for p in parts
        for ring in [p["outer"], *p["holes"]]
        for pt in ring
        if (pt[0] ** 2 + pt[1] ** 2) ** 0.5 > radius_units * 1.02
    ]
    if stray:
        print(f"[WARN] {len(stray)} vertices fall outside the clip disc")
        ok = False

    print(f"\n[ok] region disc spans {radius_units:.2f} units, city model spans ~1.0 unit for scale")
    print("\nGO" if ok else "\nCHECK WARNINGS")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
