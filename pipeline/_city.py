"""Shared city configuration loader (issue #68).

Why this exists:
    The pipeline's docs have claimed a "city-agnostic architecture" since the
    first README, but Mumbai was hardcoded in eight places: the boundary
    filename in stages 01, 03, 05, 10 and 11; the UTM zone in 01, 03, 11 and 12;
    the plausibility bbox in 01; the grid size in 01; the Earth Engine project in
    _gee_auth; and the map centre in the frontend. Standing up a second city
    meant editing all of them and hoping none were missed.

    Now every one of those reads from config/cities/<slug>.json, and the claim is
    true rather than aspirational.

Deliberately JSON rather than YAML:
    It needs no new dependency, and more usefully the frontend reads the same
    file. One config, both languages, so the map centre the browser uses and the
    bbox the pipeline validates against cannot drift apart.

What does NOT transfer between cities:
    The PCA weighting is derived from the city's own cells, so it is recomputed
    per city automatically. The plantability filter is different: its thresholds
    encode Mumbai's ecology, in particular treating WorldCover class 30 as native
    grassland to protect. Transplanted unexamined to another biome it would
    confidently recommend afforesting habitat that should not be afforested,
    which is exactly the failure Veldman 2019 warns about and which this project
    cites as its differentiator. The config carries an `ecology.calibrated` flag
    for that reason, and it should be false until a human has actually checked.
    See docs/adding-a-city.md.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config" / "cities"
DATA_DIR = ROOT / "data"

DEFAULT_CITY = "mumbai"

# The resolution the published dataset is built at. Only this one writes to the
# city's own data directory and to frontend/public; see CityConfig.data_dir.
DEFAULT_CELL_SIZE_M = 1000.0


@dataclass(frozen=True)
class CityConfig:
    slug: str
    name: str
    timezone: str
    bbox: tuple[float, float, float, float]
    boundaries_path: Path
    ward_id_field: str
    expected_ward_count: int | None
    # Which loader reads this city's boundaries (issue #111). "file" is every
    # city today; see pipeline/_boundaries.py for the alternatives.
    boundaries_adapter: str
    # The whole boundaries block, so an adapter can read its own keys without
    # every one of them becoming a field here.
    boundaries_config: dict
    cell_size_m: float
    projected_crs: str
    gee_project: str | None
    map_center: tuple[float, float]
    map_zoom: float
    ecology: dict
    raw: dict

    @property
    def bbox_lonlat(self) -> tuple[float, float, float, float]:
        """(min_lon, min_lat, max_lon, max_lat)."""
        return self.bbox

    @property
    def data_dir(self) -> Path:
        """Where this city's pipeline output lives.

        The default city writes to data/ directly and every other city to
        data/<slug>/. That asymmetry is deliberate rather than sloppy: the
        frontend, the committed snapshots, the deck and the methodology page all
        reference data/wards_hvi.geojson by that exact path, so moving Mumbai
        under data/mumbai/ would be a breaking change for no benefit while it is
        the only published city.

        What this does fix is real. Before output was namespaced, running any
        second city wrote over the first: a Pune run silently replaced Mumbai's
        547-cell grid with Pune's 322 cells at the same filename, and nothing
        complained. Verified on 2026-09-03, which is how it was found.

        Resolution namespaces the same way (issue #96), and for the same
        reason. Only the default resolution writes to the city's own directory;
        anything else gets a suffixed one, so `data/mumbai_500m/`. Putting it
        here rather than in each filename covers every artefact the run
        produces, including the ones named for what they contain rather than
        how they were built: cells.geojson, wards_hvi.geojson and the rest all
        land beside their 1 km counterparts instead of on top of them, and no
        stage downstream of the grid needed changing to get that.
        """
        if self.cell_size_m == DEFAULT_CELL_SIZE_M:
            return DATA_DIR if self.slug == DEFAULT_CITY else DATA_DIR / self.slug
        # A non-default resolution is always named, including for the default
        # city, which is the one case where the directory would otherwise be
        # data/ itself and the suffix would have nothing to attach to.
        return DATA_DIR / f"{self.slug}_{self.grid_label}"

    def out(self, filename: str) -> Path:
        """Path for one of this city's output files, creating the directory."""
        d = self.data_dir
        d.mkdir(parents=True, exist_ok=True)
        return d / filename

    @property
    def grid_label(self) -> str:
        """The grid resolution as it appears in a filename: 1km, 500m, 250m.

        Whole kilometres read as kilometres because that is how everything in
        this repo already refers to the default grid, and anything else reads
        as metres. 1000 -> "1km", 500 -> "500m", 2000 -> "2km", 250 -> "250m".
        """
        metres = self.cell_size_m
        if metres >= 1000 and metres % 1000 == 0:
            km = metres / 1000
            return f"{km:g}km"
        return f"{metres:g}m"

    def grid_path(self, suffix: str = "") -> Path:
        """Path for a grid artefact, named for this city's resolution (issue #96).

        The resolution is in the filename for the same reason the city is in the
        directory, and the failure it prevents is the one the `data_dir`
        docstring above describes, one level down.

        These paths used to be module-level constants spelling "grid_1km"
        literally, while `cell_size_m` was already configurable. Setting it to
        500 therefore did not produce a 500 m dataset: it produced 500 m cells
        written over the 1 km ones, in files still called grid_1km, with
        nothing to indicate which resolution any of them held. The only clue
        would have been the cell count, four times larger, in a file whose name
        said otherwise.

        At 1000 m every path here is byte-identical to the old constants, so
        the committed Mumbai outputs keep their names.

            grid_path()           -> data/grid_1km.geojson
            grid_path("_gee")     -> data/grid_1km_gee.geojson
            grid_path("_vectors") -> data/grid_500m_vectors.geojson  (at 500 m)
        """
        return self.out(f"grid_{self.grid_label}{suffix}.geojson")

    @property
    def publishes_to_frontend(self) -> bool:
        """Only the default city's output is what the site serves.

        A second city's run must not overwrite frontend/public/, or standing up
        Pune would swap the live Mumbai dashboard for a half-built one. A
        non-default resolution must not either: the site is built and tested
        against the 1 km dataset, and a 500 m run is an experiment until
        somebody has looked at what it does to the payload.
        """
        return self.slug == DEFAULT_CITY and self.cell_size_m == DEFAULT_CELL_SIZE_M


def utm_crs_for(bbox: tuple[float, float, float, float]) -> str:
    """Best-fit UTM EPSG code for a bounding box, from its centroid.

    A metric CRS is required for anything measured in metres: the fishnet has to
    be built in one or a "1 km" cell is not 1 km, and the hero model extrudes in
    projected space. Inheriting Mumbai's EPSG:32643 for a city in another zone
    would still produce plausible-looking output while silently distorting every
    area and distance, so this is derived rather than defaulted.

    Northern hemisphere codes are 326xx, southern 327xx.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    lon = (min_lon + max_lon) / 2
    lat = (min_lat + max_lat) / 2
    zone = int((lon + 180) / 6) + 1
    return f"EPSG:{326 if lat >= 0 else 327}{zone:02d}"


def _cell_size_override(configured: float) -> float:
    """The configured cell size, unless UCIP_CELL_SIZE_M overrides it.

    Refuses a value it cannot use rather than silently falling back to the
    config: a typo that quietly produced a 1 km run labelled as 500 m is the
    failure this whole change exists to prevent.
    """
    raw = os.environ.get("UCIP_CELL_SIZE_M")
    if raw is None or raw.strip() == "":
        return float(configured)
    try:
        metres = float(raw)
    except ValueError as exc:
        raise ValueError(f"UCIP_CELL_SIZE_M={raw!r} is not a number") from exc
    if metres <= 0:
        raise ValueError(f"UCIP_CELL_SIZE_M={raw!r} must be greater than zero")
    return metres


def load_city(slug: str | None = None) -> CityConfig:
    """Load a city config by slug.

    Resolution order: the explicit argument, then the UCIP_CITY environment
    variable, then Mumbai. The environment variable is what lets run_pipeline.py
    pass --city down to twelve subprocesses without every stage needing to parse
    the flag itself.

    UCIP_CELL_SIZE_M overrides the config's grid resolution the same way, for
    the same reason (issue #96). Running the pipeline at 500 m is an
    experiment, and an experiment should not require editing a committed config
    file that CI validates and the frontend mirrors. The override changes where
    every output lands, via CityConfig.data_dir, so a 500 m run cannot touch the
    published 1 km dataset whether it finishes or fails half way.
    """
    slug = slug or os.environ.get("UCIP_CITY") or DEFAULT_CITY
    path = CONFIG_DIR / f"{slug}.json"
    if not path.exists():
        available = sorted(p.stem for p in CONFIG_DIR.glob("*.json"))
        raise SystemExit(
            f"[FAIL] no city config at {path}. Available: {', '.join(available) or 'none'}.\n"
            f"       Create one with: python pipeline/new_city.py --slug {slug} ..."
        )

    raw = json.loads(path.read_text(encoding="utf-8"))

    bbox = tuple(raw["bbox"])
    if len(bbox) != 4:
        raise SystemExit(f"[FAIL] {path}: bbox must be [min_lon, min_lat, max_lon, max_lat].")
    if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        raise SystemExit(f"[FAIL] {path}: bbox min must be less than max on both axes, got {bbox}.")

    grid = raw.get("grid", {})
    boundaries = raw["boundaries"]
    map_cfg = raw.get("map", {})
    center = tuple(map_cfg.get("center", [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]))

    return CityConfig(
        slug=raw["slug"],
        name=raw["name"],
        timezone=raw.get("timezone", "UTC"),
        bbox=bbox,  # type: ignore[arg-type]
        boundaries_path=DATA_DIR / boundaries.get("file", ""),
        ward_id_field=boundaries["ward_id_field"],
        expected_ward_count=boundaries.get("expected_ward_count"),
        boundaries_adapter=boundaries.get("adapter", "file"),
        boundaries_config=boundaries,
        cell_size_m=_cell_size_override(grid.get("cell_size_m", DEFAULT_CELL_SIZE_M)),
        # Derived when absent, so a new city cannot silently inherit Mumbai's zone.
        projected_crs=grid.get("projected_crs") or utm_crs_for(bbox),  # type: ignore[arg-type]
        gee_project=(raw.get("gee") or {}).get("project"),
        map_center=center,  # type: ignore[arg-type]
        map_zoom=float(map_cfg.get("zoom", 11)),
        ecology=raw.get("ecology", {}),
        raw=raw,
    )


def add_city_argument(parser: argparse.ArgumentParser) -> None:
    """Adds the standard --city flag to a stage's parser."""
    parser.add_argument(
        "--city",
        default=None,
        help="City slug from config/cities/ (default: $UCIP_CITY, else mumbai).",
    )


def city_from_argv(description: str = "") -> CityConfig:
    """Parse --city from a stage's own argv and load that config.

    Stages that take no other arguments use this so they stay runnable
    standalone, which pipeline/README.md documents and which is how most
    debugging actually happens.
    """
    parser = argparse.ArgumentParser(description=description)
    add_city_argument(parser)
    args, _unknown = parser.parse_known_args()
    return load_city(args.city)
