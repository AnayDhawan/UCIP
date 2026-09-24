"""Response types for the UCIP API.

GENERATED FILE. Do not edit.

Produced by scripts/generate.py from clients/openapi.json, which the
TypeScript generator emits from frontend/src/lib/openapiSpec.ts.
Regenerate with `python scripts/generate.py`. CI regenerates and diffs,
so an API change that is not reflected here fails the build rather than
shipping a client that describes the wrong shapes.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class WardGeomGeojson(TypedDict, total=False):
    """GeoJSON geometry. Only present when `geometry=true` was requested."""

    type: str
    coordinates: list[Any]


class Ward(TypedDict, total=False):
    ward_id: str
    """
    BMC ward code.
    """
    hvi: float | None
    """
    Heat Vulnerability Index, 0-100. Higher is more vulnerable.
    """
    rank: int | None
    """
    1 is the most vulnerable of 24.
    """
    n_cells: int | None
    """
    1 km grid cells in this ward.
    """
    contrib: dict[str, float] | None
    """
    Per-factor contribution to the score (weight x z-score). Sums to the
    pre-rescale index, so a ward's score decomposes exactly into its
    drivers.
    """
    dominant_factor: str | None
    """
    The indicator with the largest absolute contribution to this ward's
    score.
    """
    dominant_share: float | None
    """
    That indicator's share of total absolute contribution, 0 to 1. An even
    spread across the seven indicators is about 0.14.
    """
    single_factor_dominated: bool | None
    """
    True when one indicator accounts for half or more of the movement in the
    score, so the ranking is effectively driven by that one measure.
    """
    geom_geojson: WardGeomGeojson | None
    """
    GeoJSON geometry. Only present when `geometry=true` was requested.
    """


class Recommendation(TypedDict, total=False):
    ward_id: str
    """
    Omitted on /wards/{wardId}, where the ward is already the subject of the
    response.
    """
    intervention: str
    rationale: str
    """
    Why this rule fired for this ward.
    """
    citation: str
    """
    The paper backing the intervention.
    """
    priority: int
    """
    1 is highest priority within the ward.
    """
    cell_count: int | None
    """
    How many grid cells in the ward triggered this rule.
    """


class CellGeomGeojson(TypedDict, total=False):
    """GeoJSON geometry. Only present when `geometry=true` was requested."""

    type: str
    coordinates: list[Any]


class Cell(TypedDict, total=False):
    """
    One 1 km analysis cell. These are the measurements the ward scores are
    built from, published so the rollup can be checked rather than trusted.
    """

    grid_id: str | int
    ward_id: str
    lst_c: float | None
    """
    Dry-season land surface temperature, Celsius.
    """
    ndvi: float | None
    """
    Normalised difference vegetation index, -1 to 1.
    """
    ndvi_prev: float | None
    """
    NDVI in the previous comparison window.
    """
    pop_density_km2: float | None
    elderly_pct: float | None
    """
    Share of population aged 60 or over.
    """
    slum_pct: float | None
    hospital_dist_m: float | None
    """
    Distance to the nearest hospital, metres.
    """
    impervious_pct: float | None
    hvi: float | None
    plantable: bool | None
    """
    Whether the ecological filter allows tree planting here. False on native
    open habitat, water, wetland, mangrove and heavily sealed cells.
    """
    worldcover_class: int | None
    """
    ESA WorldCover class code.
    """
    geom_geojson: CellGeomGeojson | None
    """
    GeoJSON geometry. Only present when `geometry=true` was requested.
    """


class MetaCoverageCities(TypedDict, total=False):
    name: str
    wards: int | None


class MetaCoverage(TypedDict, total=False):
    cities: list[MetaCoverageCities]
    note: str


class MetaCounts(TypedDict, total=False):
    wards: int | None
    recommendations: int | None
    citations: int | None


class MetaCompositeWindow(TypedDict, total=False):
    """
    The Landsat dry-season window the figures were computed from. This is
    older than generated_at and is the one that says how old the
    measurements actually are.
    """

    start: str
    end: str


class MetaMethod(TypedDict, total=False):
    index: str
    weighting: str
    """
    Says explicitly when the PCA weighting fell back to published literature
    weights, because that changes how the scores were derived.
    """
    explainability: str
    limitations_url: str


class MetaLicense(TypedDict, total=False):
    code: str
    data: str


class MetaLinks(TypedDict, total=False):
    documentation: str
    methodology: str
    repository: str


class Meta(TypedDict, total=False):
    name: str
    api_version: str
    description: str
    coverage: MetaCoverage
    counts: MetaCounts
    generated_at: str | None
    """
    When the pipeline last produced this data. Null until a refresh run has
    committed a run log; a guessed date would defeat the point of the field.
    """
    composite_window: MetaCompositeWindow | None
    """
    The Landsat dry-season window the figures were computed from. This is
    older than generated_at and is the one that says how old the
    measurements actually are.
    """
    method: MetaMethod
    database_configured: bool
    license: MetaLicense
    links: MetaLinks


class ApiErrorError(TypedDict, total=False):
    status: int
    message: str
    hint: str
    """
    Present when there is a useful next step.
    """


class ApiError(TypedDict, total=False):
    error: ApiErrorError


class WardListResponse(TypedDict, total=False):
    source: Literal["database", "snapshot"]
    """
    Which backend answered. `snapshot` means the database was unavailable
    and the committed static files were served instead, at most one refresh
    behind.
    """
    count: int
    wards: list[Ward]


class WardDetailResponse(TypedDict, total=False):
    source: Literal["database", "snapshot"]
    """
    Which backend answered. `snapshot` means the database was unavailable
    and the committed static files were served instead, at most one refresh
    behind.
    """
    ward: Ward
    recommendations: list[Recommendation]


class LookupResponseQuery(TypedDict, total=False):
    """The coordinate as parsed, echoed back."""

    lat: float
    lon: float


class LookupResponse(TypedDict, total=False):
    source: Literal["database", "snapshot"]
    """
    Which backend answered. `snapshot` means the database was unavailable
    and the committed static files were served instead, at most one refresh
    behind.
    """
    query: LookupResponseQuery
    """
    The coordinate as parsed, echoed back.
    """
    ward: Ward
    top_recommendation: Recommendation | None
    """
    The highest-priority recommendation for the containing ward, if any.
    """


class RecommendationListResponse(TypedDict, total=False):
    source: Literal["database", "snapshot"]
    """
    Which backend answered. `snapshot` means the database was unavailable
    and the committed static files were served instead, at most one refresh
    behind.
    """
    count: int
    recommendations: list[Recommendation]


class CellListResponse(TypedDict, total=False):
    source: Literal["database", "snapshot"]
    """
    Which backend answered. `snapshot` means the database was unavailable
    and the committed static files were served instead, at most one refresh
    behind.
    """
    count: int
    cells: list[Cell]


__all__ = [
    "ApiError",
    "Cell",
    "CellListResponse",
    "LookupResponse",
    "Meta",
    "Recommendation",
    "RecommendationListResponse",
    "Ward",
    "WardDetailResponse",
    "WardListResponse",
]
