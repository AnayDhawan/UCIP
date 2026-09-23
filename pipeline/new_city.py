"""Scaffold a city config that validates on the first try (issue #108).

Adding a city should not mean copying Mumbai's config and editing it by hand
until the errors stop. Copying is how a city inherits Mumbai's UTM zone, which
silently distorts every area and distance in the pipeline while producing output
that looks entirely plausible, and how it inherits Mumbai's coastal ecology
calibration, which is the most damaging mistake available here.

This takes a name and a bounding box and writes a config with the derived values
already correct:

    python new_city.py --slug pune --name Pune --bbox 73.7 18.4 74.0 18.65 \\
        --boundaries pune_wards.geojson --ward-id-field name

Derived rather than asked for:
    projected_crs   the UTM zone for the bbox centroid (pipeline/_city.py)
    map.center      the bbox centre, in Leaflet's [lat, lon] order, which is the
                    reverse of the bbox's own order and an easy thing to get
                    wrong by hand

Deliberately not derived:
    ecology.calibrated is written as false, with a note saying why. A scaffolder
    that marked a new city as calibrated would be asserting that someone had
    reviewed its biome against the restoration literature, which by definition
    nobody has. It is the one field that has to stay a human decision.

The output is checked against config/city.schema.json before it is written, so
a scaffold that would not validate fails here rather than in CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_DIR))

from _city import utm_crs_for  # noqa: E402

ROOT = PIPELINE_DIR.parent
CONFIG_DIR = ROOT / "config" / "cities"
SCHEMA_PATH = ROOT / "config" / "city.schema.json"
DATA_DIR = ROOT / "data"

DEFAULT_CELL_SIZE_M = 1000

ECOLOGY_NOTE = (
    "NOT calibrated. The plantability filter encodes Mumbai's coastal ecology: "
    "WorldCover class 30 treated as native grassland to protect, an impervious "
    "threshold for physical planting room, and thresholds at local percentiles. "
    "Applied unexamined to a different biome it risks recommending afforestation "
    "of habitat that should stay open, which is the failure Veldman 2019 warns "
    "about. Review against this region's restoration literature before trusting "
    "any plantability output, then set calibrated to true. "
    "See docs/adding-a-city.md."
)


def build_config(
    slug: str,
    name: str,
    bbox: list[float],
    boundaries_file: str,
    ward_id_field: str,
    country: str | None,
    timezone: str,
    cell_size_m: int,
    expected_ward_count: int | None,
    source: str | None,
    source_url: str | None,
    gee_project: str | None,
) -> dict:
    min_lon, min_lat, max_lon, max_lat = bbox

    config: dict = {
        "$schema": "../city.schema.json",
        "slug": slug,
        "name": name,
    }
    if country:
        config["country"] = country

    config["timezone"] = timezone
    config["bbox"] = bbox

    boundaries: dict = {"file": boundaries_file, "ward_id_field": ward_id_field}
    if source:
        boundaries["source"] = source
    if source_url:
        boundaries["source_url"] = source_url
    if expected_ward_count is not None:
        boundaries["expected_ward_count"] = expected_ward_count
    config["boundaries"] = boundaries

    config["grid"] = {
        "cell_size_m": cell_size_m,
        # Derived, not inherited. This is the field that silently distorts every
        # area and distance in the pipeline when it is copied from another city.
        "projected_crs": utm_crs_for(tuple(bbox)),
    }

    if gee_project:
        config["gee"] = {"project": gee_project}

    config["map"] = {
        # Leaflet order: [lat, lon]. The bbox is [lon, lat, lon, lat].
        "center": [
            round((min_lat + max_lat) / 2, 6),
            round((min_lon + max_lon) / 2, 6),
        ],
        "zoom": 12,
    }

    config["ecology"] = {
        "biome": "TODO: name the biome, e.g. 'Deccan plateau, semi-arid to tropical dry deciduous'",
        "calibrated": False,
        "notes": ECOLOGY_NOTE,
    }

    return config


def validate(config: dict) -> list[str]:
    """Schema errors in the scaffolded config, with the field that caused each."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
    return [
        f"{'.'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(validator.iter_errors(config), key=lambda e: list(e.absolute_path))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--slug", required=True, help="Lowercase id, and the filename.")
    parser.add_argument("--name", required=True, help="Display name, e.g. Pune.")
    parser.add_argument(
        "--bbox", required=True, nargs=4, type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Bounding box, GeoJSON order.",
    )
    parser.add_argument("--boundaries", required=True,
                        help="Ward boundary filename, relative to data/.")
    parser.add_argument("--ward-id-field", required=True,
                        help="Property in the boundary file holding the ward id.")
    parser.add_argument("--country")
    parser.add_argument("--timezone", default="Asia/Kolkata")
    parser.add_argument("--cell-size-m", type=int, default=DEFAULT_CELL_SIZE_M)
    parser.add_argument("--expected-ward-count", type=int)
    parser.add_argument("--source", help="Where the boundaries came from.")
    parser.add_argument("--source-url")
    parser.add_argument("--gee-project", help="Earth Engine project id.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing config for this slug.")
    parser.add_argument("--stdout", action="store_true",
                        help="Print the config instead of writing it.")
    args = parser.parse_args()

    slug = args.slug.strip().lower()
    if slug != args.slug:
        print(f"[note] slug normalised to '{slug}'")

    min_lon, min_lat, max_lon, max_lat = args.bbox
    if min_lon >= max_lon or min_lat >= max_lat:
        print(f"[FAIL] bbox min must be below max on both axes, got {args.bbox}")
        return 1

    config = build_config(
        slug=slug,
        name=args.name,
        bbox=list(args.bbox),
        boundaries_file=args.boundaries,
        ward_id_field=args.ward_id_field,
        country=args.country,
        timezone=args.timezone,
        cell_size_m=args.cell_size_m,
        expected_ward_count=args.expected_ward_count,
        source=args.source,
        source_url=args.source_url,
        gee_project=args.gee_project,
    )

    errors = validate(config)
    if errors:
        print("[FAIL] the scaffolded config does not validate, which is a bug in this script:")
        for error in errors:
            print(f"  {error}")
        return 1

    if args.stdout:
        print(json.dumps(config, indent=2))
        return 0

    out_path = CONFIG_DIR / f"{slug}.json"
    if out_path.exists() and not args.force:
        print(f"[FAIL] {out_path.relative_to(ROOT)} already exists. Pass --force to overwrite.")
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] wrote {out_path.relative_to(ROOT)}")
    print(f"[ok] projected_crs derived as {config['grid']['projected_crs']}")
    print(f"[ok] map.center derived as {config['map']['center']} (lat, lon)")

    boundary_path = DATA_DIR / args.boundaries
    if not boundary_path.exists():
        print(f"\n[next] put the ward boundaries at {boundary_path.relative_to(ROOT)}")

    print("\n[next] ecology.calibrated is false, deliberately. The plantability")
    print("       filter encodes Mumbai's ecology and must be reviewed against this")
    print("       region's restoration literature before it is trusted here.")
    print(f"\n[next] python validate_cities.py --city {slug} --allow-missing-data")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
