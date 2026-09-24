"""The UCIP API client (issue #104).

The audience for this package works in notebooks, so the frame methods are the
point and the raw JSON methods are what they are built on. Both are public:
`wards()` gives you exactly what the API sent, `wards_frame()` gives you
something you can group and plot.

Three decisions worth stating once, here:

Frames are built from the bulk export, not by paging. `wards_geo()` and
`cells_geo()` are one edge-cached request for the whole dataset. Paging the
per-record endpoints to assemble a frame would be slower, would put a
free-tier database in the request path repeatedly, and is the surest way to
meet the rate limiter.

The `contrib` mapping is flattened into `contrib_*` columns. A DataFrame column
holding dicts cannot be grouped, plotted or described, which defeats the reason
someone asked for a DataFrame. The nested form is still there in `wards()`.

pandas and geopandas are required dependencies but are imported lazily.
Required, because the whole point of this package is that three lines give you
a GeoDataFrame, and an extras flag to reach that is friction aimed at exactly
the audience the package is for. Lazy, because importing geopandas costs
seconds and pulls in GDAL bindings, and `meta()` should not pay that. If an
import fails anyway, on a `--no-deps` install or a half-built environment, the
error says which package is missing rather than surfacing an ImportError from
somewhere inside this module.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal, Mapping
from urllib.parse import quote

import requests

from .errors import MissingDependency, UcipHTTPError, UcipNetworkError
from .models import (
    ApiError,
    CellListResponse,
    LookupResponse,
    Meta,
    RecommendationListResponse,
    Ward,
    WardDetailResponse,
    WardListResponse,
)

if TYPE_CHECKING:  # pragma: no cover - import-time only for type checkers
    import geopandas as gpd
    import pandas as pd

DEFAULT_BASE_URL = "https://uciplatform.vercel.app/api/v1"

Dataset = Literal["cells", "wards"]

__all__ = ["Ucip", "DEFAULT_BASE_URL"]


def _require(module: str) -> Any:
    """Import a dependency lazily, naming it clearly if it is not there."""
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise MissingDependency(
            f"{module} is required for this method but could not be imported. "
            f"It is a dependency of this package, so this usually means a "
            f"--no-deps install or a broken environment. Fix it with: "
            f"pip install --upgrade ucip"
        ) from exc


class Ucip:
    """A client for the public UCIP API.

    No authentication, no key, no account. Everything served is public and
    read-only.

    >>> wards = Ucip().wards_geo()          # doctest: +SKIP
    >>> wards.plot(column="hvi")            # doctest: +SKIP
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 30.0,
        session: requests.Session | None = None,
        user_agent: str | None = None,
    ) -> None:
        # Trailing slashes are stripped so a base URL copied with one does not
        # produce a double slash in every path.
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        if user_agent:
            self._session.headers["user-agent"] = user_agent
        self._session.headers.setdefault("accept", "application/json")

    # ------------------------------------------------------------------
    # Raw endpoints
    # ------------------------------------------------------------------

    def meta(self) -> Meta:
        """What this deployment serves: coverage, counts, method, data vintage."""
        return self._get("/meta")

    def wards(self, *, limit: int | None = None, geometry: bool | None = None) -> WardListResponse:
        """Every ward, ranked most vulnerable first."""
        return self._get("/wards", limit=limit, geometry=geometry)

    def ward(self, ward_id: str) -> WardDetailResponse:
        """One ward and its ranked recommendations.

        Encodes the ward code, which matters: `F/N` is a real code and the
        slash breaks the path if it goes through unencoded.
        """
        if not ward_id or not ward_id.strip():
            raise ValueError("ward_id is required")
        return self._get(f"/wards/{quote(ward_id.strip(), safe='')}")

    def lookup(self, lat: float, lon: float) -> LookupResponse:
        """The ward containing a coordinate, with its top recommendation."""
        # Checked here rather than spending a round trip to be told 400.
        if not -90 <= lat <= 90:
            raise ValueError(f"lat must be between -90 and 90, got {lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"lon must be between -180 and 180, got {lon}")
        return self._get("/lookup", lat=lat, lon=lon)

    def recommendations(
        self, *, ward: str | None = None, limit: int | None = None
    ) -> RecommendationListResponse:
        """Nature-based-solution recommendations, optionally for one ward."""
        return self._get("/recommendations", ward=ward, limit=limit)

    def cells(
        self,
        *,
        ward: str | None = None,
        bbox: str | None = None,
        limit: int | None = None,
        geometry: bool | None = None,
    ) -> CellListResponse:
        """The 1 km analysis grid the ward scores are built from."""
        return self._get("/cells", ward=ward, bbox=bbox, limit=limit, geometry=geometry)

    def export(self, dataset: Dataset = "cells") -> dict[str, Any]:
        """The whole dataset as a GeoJSON FeatureCollection, in one request."""
        return self._get("/export", dataset=dataset, format="geojson")

    def export_csv(self, dataset: Dataset = "cells") -> str:
        """The whole dataset as CSV text, with the feature centre as lon/lat."""
        response = self._request("/export", {"dataset": dataset, "format": "csv"}, accept="text/csv")
        return response.text

    # ------------------------------------------------------------------
    # Frames
    # ------------------------------------------------------------------

    def wards_frame(self) -> "pd.DataFrame":
        """Every ward as a DataFrame, indexed by ward code, ranked first.

        The per-factor contributions arrive as a nested mapping and are
        flattened into `contrib_*` columns, because a column of dicts cannot be
        grouped, plotted or described.
        """
        pd = _require("pandas")
        rows = [self._flatten_ward(w) for w in self.wards().get("wards", [])]
        frame = pd.DataFrame(rows)
        return self._index_by_ward(frame)

    def cells_frame(self, *, ward: str | None = None) -> "pd.DataFrame":
        """The analysis grid as a DataFrame, indexed by cell id."""
        pd = _require("pandas")
        # 1000 is the endpoint's ceiling and comfortably above the 541 cells
        # Mumbai has, so this is one request rather than a paging loop.
        payload = self.cells(ward=ward, limit=1000)
        frame = pd.DataFrame(list(payload.get("cells", [])))
        if "grid_id" in frame.columns:
            frame = frame.set_index("grid_id")
        return frame

    def recommendations_frame(self, *, ward: str | None = None) -> "pd.DataFrame":
        """Every recommendation as a DataFrame, with its citation intact.

        The citation column is not optional and is not dropped. A
        recommendation to plant trees somewhere, separated from the paper it
        rests on, is exactly the artefact this project exists not to produce.
        """
        pd = _require("pandas")
        payload = self.recommendations(ward=ward, limit=500)
        return pd.DataFrame(list(payload.get("recommendations", [])))

    def wards_geo(self) -> "gpd.GeoDataFrame":
        """Every ward as a GeoDataFrame, with geometry, in EPSG:4326.

        One cached request for the whole dataset. This is the three-line path:

        >>> import ucip                          # doctest: +SKIP
        >>> wards = ucip.Ucip().wards_geo()      # doctest: +SKIP
        >>> wards.plot(column="hvi")             # doctest: +SKIP
        """
        return self._geo("wards")

    def cells_geo(self) -> "gpd.GeoDataFrame":
        """Every 1 km grid cell as a GeoDataFrame, with geometry, in EPSG:4326."""
        return self._geo("cells")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _geo(self, dataset: Dataset) -> "gpd.GeoDataFrame":
        gpd = _require("geopandas")
        collection = self.export(dataset)
        features = collection.get("features", [])
        if not features:
            raise UcipHTTPError(
                200,
                f"{self.base_url}/export",
                detail=f"The {dataset} export came back with no features.",
                body=json.dumps(collection)[:500],
            )

        frame = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

        # from_features keeps the properties as they are, so the ward frame
        # gets the same contrib_* treatment the plain frame gets. The export
        # already flattens them, so this only has to handle the nested form if
        # a future export stops doing that.
        if "contrib" in frame.columns:
            pd = _require("pandas")
            contrib = pd.json_normalize(frame["contrib"]).add_prefix("contrib_")
            contrib.index = frame.index
            frame = frame.drop(columns=["contrib"]).join(contrib)

        return self._index_by_ward(frame) if dataset == "wards" else frame

    @staticmethod
    def _flatten_ward(ward: Ward) -> dict[str, Any]:
        row = {k: v for k, v in ward.items() if k != "contrib"}
        for factor, value in (ward.get("contrib") or {}).items():
            row[f"contrib_{factor}"] = value
        return row

    @staticmethod
    def _index_by_ward(frame: "pd.DataFrame") -> "pd.DataFrame":
        """Index by ward code and sort by rank, when both columns are there."""
        if "rank" in frame.columns:
            frame = frame.sort_values("rank")
        if "ward_id" in frame.columns:
            frame = frame.set_index("ward_id")
        return frame

    def _get(self, path: str, **params: Any) -> Any:
        return self._request(path, params).json()

    def _request(
        self, path: str, params: Mapping[str, Any], *, accept: str | None = None
    ) -> requests.Response:
        # None means "not specified", which has to mean the parameter is absent
        # rather than the string "None". Booleans go over the wire lowercase,
        # which is what the API parses.
        query = {
            key: ("true" if value is True else "false" if value is False else value)
            for key, value in params.items()
            if value is not None
        }

        url = f"{self.base_url}{path}"
        headers = {"accept": accept} if accept else None

        try:
            response = self._session.get(url, params=query, timeout=self.timeout, headers=headers)
        except requests.RequestException as exc:
            raise UcipNetworkError(f"Request to {url} failed: {exc}") from exc

        if not response.ok:
            raise self._http_error(response)
        return response

    @staticmethod
    def _http_error(response: requests.Response) -> UcipHTTPError:
        detail: str | None = None
        hint: str | None = None
        try:
            # An error from an edge proxy rather than the API itself is HTML,
            # not the JSON envelope, and failing to parse it must not replace a
            # useful 502 with a JSON decode error.
            payload: ApiError = response.json()
            error = payload.get("error") or {}
            detail = error.get("message")
            hint = error.get("hint")
        except ValueError:
            pass

        retry_after: float | None = None
        raw = response.headers.get("retry-after")
        if raw:
            try:
                retry_after = float(raw)
            except ValueError:
                retry_after = None

        return UcipHTTPError(
            response.status_code,
            response.url,
            detail=detail,
            hint=hint,
            retry_after=retry_after,
            body=response.text,
        )
