"""One way to load ward boundaries, whatever the source is (issue #111).

The problem:
    Boundaries came from Datameet, which is India only, and the loading was
    inline in four stages. Each one read the file, synthesised a gid if the
    source lacked one, then selected and renamed columns by hand. Four copies
    of the same twelve lines, and they had already drifted: 11_hero_city.py
    renamed a hardcoded "name" column rather than the configured
    ward_id_field, which works for Mumbai and Pune only because both happen to
    use "name" and would silently produce no ward_id column at all for a city
    that does not.

    That is the whole argument for this module. A city outside India needs a
    different source, and a template whose loading is copy-pasted per stage
    cannot take one.

What a caller gets:
    A GeoDataFrame with exactly ward_id, ward_gid and geometry, in WGS84, ids
    unique and non-null, whatever the source was. Stages stop knowing where
    boundaries come from.

Adapters:
    file    a boundary file already in data/. What every city uses today.
    osm     OpenStreetMap administrative relations, for a city mapped in OSM
            but with no national open-data portal.
    gadm    GADM administrative areas, which cover every country at a coarser
            resolution than a municipal source.

    Only `file` has been run against real data. The other two are written from
    their documented interfaces and are unverified; see the note on each.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    import geopandas as gpd

WGS84 = "EPSG:4326"


class BoundaryError(RuntimeError):
    """Raised when boundaries cannot be loaded or do not survive validation."""


def normalise(
    frame: "gpd.GeoDataFrame",
    ward_id_field: str,
    label: str = "boundaries",
) -> "gpd.GeoDataFrame":
    """Reduce any source's frame to ward_id, ward_gid and geometry in WGS84.

    The one place the column contract is applied, so a stage cannot get it
    subtly wrong and a new adapter cannot invent its own spelling.
    """
    if ward_id_field not in frame.columns:
        raise BoundaryError(
            f"{label}: no '{ward_id_field}' column. Found: {sorted(frame.columns)}. "
            "Set boundaries.ward_id_field in the city config to one of these."
        )

    out = frame.copy()

    # A source with no CRS is assumed to be WGS84, which is what every
    # published boundary file in this project is. Assuming silently would be
    # wrong for a projected source, so only an absent CRS is filled in.
    if out.crs is None:
        out = out.set_crs(WGS84)
    elif out.crs.to_string() != WGS84:
        out = out.to_crs(WGS84)

    # gid is Datameet's own numeric id and is not guaranteed anywhere else.
    if "gid" not in out.columns:
        out = out.assign(gid=range(1, len(out) + 1))

    out = out[["gid", ward_id_field, "geometry"]].rename(
        columns={"gid": "ward_gid", ward_id_field: "ward_id"}
    )

    # Ward ids reach output filenames, API paths and the published dataset, so
    # a null or duplicated one is a data problem worth failing on rather than
    # discovering later as two wards sharing a row.
    if out["ward_id"].isna().any():
        n = int(out["ward_id"].isna().sum())
        raise BoundaryError(f"{label}: {n} feature(s) have no '{ward_id_field}' value.")

    duplicates = out["ward_id"][out["ward_id"].duplicated()].unique().tolist()
    if duplicates:
        raise BoundaryError(
            f"{label}: duplicate ward id(s) {duplicates}. "
            f"'{ward_id_field}' does not uniquely identify a ward in this source."
        )

    out["ward_id"] = out["ward_id"].astype(str)
    return out


def _from_file(city: Any) -> "gpd.GeoDataFrame":
    """A boundary file already in data/. Every city today."""
    import geopandas as gpd

    path = city.boundaries_path
    if not path.exists():
        raise BoundaryError(
            f"boundary file {path} not found. Download it first; "
            "see docs/adding-a-city.md."
        )
    return gpd.read_file(path)


def _from_osm(city: Any) -> "gpd.GeoDataFrame":
    """Administrative relations from OpenStreetMap.

    For a city that is well mapped in OSM but has no national open-data
    portal, which is most of the world outside the handful of countries with a
    Datameet equivalent.

    UNVERIFIED. Written from osmnx's documented interface and never run
    against a real city, because doing so needs a live Overpass query for a
    city this project does not yet have. Treat the first run as the test.
    """
    import osmnx as ox

    config = getattr(city, "boundaries_config", {}) or {}
    place = config.get("osm_place")
    admin_level = config.get("osm_admin_level")

    if not place:
        raise BoundaryError(
            "the osm adapter needs boundaries.osm_place, e.g. 'Nairobi, Kenya'."
        )

    tags: dict[str, Any] = {"boundary": "administrative"}
    if admin_level is not None:
        tags["admin_level"] = str(admin_level)

    frame = ox.features_from_place(place, tags=tags)
    # Overpass returns nodes and ways alongside the relations; only areas are
    # ward boundaries.
    frame = frame[frame.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    if frame.empty:
        raise BoundaryError(
            f"OSM returned no administrative areas for {place!r} "
            f"at admin_level {admin_level!r}."
        )
    return frame.reset_index()


def _from_gadm(city: Any) -> "gpd.GeoDataFrame":
    """Administrative areas from GADM.

    Covers every country, at a coarser resolution than a municipal source.
    The fallback when a city has neither an open-data portal nor good OSM
    admin coverage.

    UNVERIFIED, as above. GADM is a large download and pinning a version
    matters, so the URL is built from the config rather than guessed.
    """
    import geopandas as gpd

    config = getattr(city, "boundaries_config", {}) or {}
    country = config.get("gadm_country")
    level = config.get("gadm_level")

    if not country or level is None:
        raise BoundaryError(
            "the gadm adapter needs boundaries.gadm_country (ISO3, e.g. 'KEN') "
            "and boundaries.gadm_level (e.g. 2)."
        )

    version = config.get("gadm_version", "4.1")
    url = (
        f"https://geodata.ucdavis.edu/gadm/gadm{version}/json/"
        f"gadm41_{country}_{level}.json"
    )
    try:
        return gpd.read_file(url)
    except Exception as exc:
        raise BoundaryError(f"could not read GADM level {level} for {country}: {exc}") from exc


ADAPTERS = {
    "file": _from_file,
    "osm": _from_osm,
    "gadm": _from_gadm,
}


def load_boundaries(city: Any) -> "gpd.GeoDataFrame":
    """Ward boundaries for a city, normalised, whatever the source."""
    adapter_name = getattr(city, "boundaries_adapter", None) or "file"

    adapter = ADAPTERS.get(adapter_name)
    if adapter is None:
        raise BoundaryError(
            f"unknown boundaries adapter {adapter_name!r}. "
            f"Known: {', '.join(sorted(ADAPTERS))}."
        )

    frame = adapter(city)
    normalised = normalise(frame, city.ward_id_field, label=f"{city.slug} boundaries")

    expected = getattr(city, "expected_ward_count", None)
    if expected is not None and len(normalised) != expected:
        raise BoundaryError(
            f"{city.slug}: expected {expected} wards, the {adapter_name} source "
            f"returned {len(normalised)}."
        )

    return normalised
