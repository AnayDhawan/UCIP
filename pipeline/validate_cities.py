"""Validate every city config against the schema, and against reality (issue #68 / D1).

Why this runs in CI:
    A malformed city config should fail in seconds, not forty minutes into an
    Earth Engine run that then writes half a dataset. Most of these checks cost
    nothing and catch the mistakes that are actually easy to make when copying
    Mumbai's config for a new city.

Beyond schema conformance, this checks things a JSON schema cannot:
    - the boundary file exists and parses, and has the ward id field named
    - the boundaries actually fall inside the declared bbox, which is the check
      that catches a copied-and-not-edited bbox
    - the ward count matches what the config claims
    - the projected CRS is plausible for the bbox, since inheriting another
      city's UTM zone silently distorts every area and distance while still
      producing output that looks fine
    - ecology.calibrated is present, because an uncalibrated plantability filter
      applied to a new biome is the most damaging mistake available here

Run:
    python pipeline/validate_cities.py            # all cities
    python pipeline/validate_cities.py --city pune
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config" / "cities"
SCHEMA_PATH = ROOT / "config" / "city.schema.json"
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _city import utm_crs_for  # noqa: E402


def check_required(cfg: dict, schema: dict, errors: list[str], label: str) -> None:
    for key in schema.get("required", []):
        if key not in cfg:
            errors.append(f"{label}: missing required key '{key}'")


def validate(path: Path, schema: dict, strict_geo: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    label = path.name

    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{label}: not valid JSON ({exc})"], []

    check_required(cfg, schema, errors, label)
    if errors:
        return errors, warnings

    if cfg["slug"] != path.stem:
        errors.append(f"{label}: slug '{cfg['slug']}' does not match filename '{path.stem}'")

    bbox = cfg.get("bbox", [])
    if len(bbox) != 4:
        errors.append(f"{label}: bbox needs 4 numbers [min_lon, min_lat, max_lon, max_lat]")
        return errors, warnings

    min_lon, min_lat, max_lon, max_lat = bbox
    if min_lon >= max_lon or min_lat >= max_lat:
        errors.append(f"{label}: bbox min must be below max on both axes, got {bbox}")
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        errors.append(f"{label}: longitudes out of range in bbox {bbox}")
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        errors.append(f"{label}: latitudes out of range in bbox {bbox}")

    grid = cfg.get("grid", {})
    declared_crs = grid.get("projected_crs")
    if declared_crs:
        expected = utm_crs_for(tuple(bbox))
        if declared_crs != expected:
            # A warning rather than an error: a city straddling a zone boundary
            # may legitimately pin a neighbouring zone. But it should be a
            # decision, not an inherited value nobody looked at.
            warnings.append(
                f"{label}: projected_crs {declared_crs} is not the UTM zone for this bbox "
                f"({expected}). Intentional for a zone-straddling city; otherwise it is a "
                f"copied value and every area in the pipeline will be distorted."
            )

    center = cfg.get("map", {}).get("center")
    if center and len(center) == 2:
        lat, lon = center
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            errors.append(
                f"{label}: map.center [{lat}, {lon}] is outside the bbox. Note the order is "
                f"[lat, lon], which is Leaflet's, not GeoJSON's."
            )

    ecology = cfg.get("ecology", {})
    if "calibrated" not in ecology:
        warnings.append(
            f"{label}: ecology.calibrated is unset. The plantability filter encodes Mumbai's "
            f"ecology; state explicitly whether it has been reviewed for this city."
        )
    elif ecology.get("calibrated") is False:
        warnings.append(
            f"{label}: ecology.calibrated is false, so this city's plantability recommendations "
            f"are not trustworthy yet. Expected for a new city; see docs/adding-a-city.md."
        )

    # ------------------------------------------------------------- geometry --
    boundaries = cfg.get("boundaries", {})
    bpath = DATA_DIR / boundaries.get("file", "")
    if not bpath.exists():
        (errors if strict_geo else warnings).append(
            f"{label}: boundary file {bpath.relative_to(ROOT)} not found"
        )
        return errors, warnings

    try:
        import geopandas as gpd
    except ImportError:
        warnings.append(f"{label}: geopandas unavailable, skipped geometry checks")
        return errors, warnings

    try:
        gdf = gpd.read_file(bpath)
    except Exception as exc:
        errors.append(f"{label}: boundary file failed to parse ({exc})")
        return errors, warnings

    field = boundaries.get("ward_id_field")
    if field not in gdf.columns:
        errors.append(
            f"{label}: ward_id_field '{field}' not in boundary file. Columns: {list(gdf.columns)}"
        )

    expected_n = boundaries.get("expected_ward_count")
    if expected_n is not None and len(gdf) != expected_n:
        errors.append(f"{label}: expected {expected_n} wards, boundary file has {len(gdf)}")

    b_minx, b_miny, b_maxx, b_maxy = gdf.total_bounds
    if not (min_lon <= b_minx and b_maxx <= max_lon and min_lat <= b_miny and b_maxy <= max_lat):
        errors.append(
            f"{label}: boundaries {[round(v, 3) for v in gdf.total_bounds]} fall outside the "
            f"declared bbox {bbox}. Usually a bbox copied from another city."
        )

    n_invalid = int((~gdf.geometry.is_valid).sum())
    if n_invalid:
        warnings.append(f"{label}: {n_invalid} invalid geometries; they will be repaired on load")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", help="Validate only this slug.")
    parser.add_argument(
        "--allow-missing-data",
        action="store_true",
        help="Treat an absent boundary file as a warning. Used in CI, where the large "
        "GeoJSON files are present but a contributor's branch may not have downloaded one.",
    )
    args = parser.parse_args()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    paths = sorted(CONFIG_DIR.glob("*.json"))
    if args.city:
        paths = [p for p in paths if p.stem == args.city]
        if not paths:
            print(f"[FAIL] no config for '{args.city}'")
            return 1

    if not paths:
        print("[FAIL] no city configs found")
        return 1

    total_errors = 0
    for path in paths:
        errors, warnings = validate(path, schema, strict_geo=not args.allow_missing_data)
        for w in warnings:
            print(f"[WARN] {w}")
        for e in errors:
            print(f"[FAIL] {e}")
        if not errors:
            print(f"[ok]   {path.stem}")
        total_errors += len(errors)

    print(f"\n{'GO' if not total_errors else 'FAILED'}: {len(paths)} config(s), {total_errors} error(s).")
    return 0 if not total_errors else 1


if __name__ == "__main__":
    sys.exit(main())
