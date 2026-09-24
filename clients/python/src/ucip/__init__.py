"""Python client for the UCIP API.

Mumbai ward-level heat vulnerability data and cited nature-based cooling
recommendations, as pandas and geopandas frames.

    >>> import ucip                          # doctest: +SKIP
    >>> wards = ucip.Ucip().wards_geo()      # doctest: +SKIP
    >>> wards.plot(column="hvi")             # doctest: +SKIP

No authentication, no key, no account. See <https://uciplatform.vercel.app>
for the dashboard and <https://uciplatform.vercel.app/methodology> for what
the numbers mean and where they do not apply.
"""

from __future__ import annotations

from .client import DEFAULT_BASE_URL, Ucip
from .errors import (
    MissingDependency,
    UcipError,
    UcipHTTPError,
    UcipNetworkError,
)
from .models import (
    ApiError,
    Cell,
    CellListResponse,
    LookupResponse,
    Meta,
    Recommendation,
    RecommendationListResponse,
    Ward,
    WardDetailResponse,
    WardListResponse,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_BASE_URL",
    "ApiError",
    "Cell",
    "CellListResponse",
    "LookupResponse",
    "Meta",
    "MissingDependency",
    "Recommendation",
    "RecommendationListResponse",
    "Ucip",
    "UcipError",
    "UcipHTTPError",
    "UcipNetworkError",
    "Ward",
    "WardDetailResponse",
    "WardListResponse",
    "__version__",
]
