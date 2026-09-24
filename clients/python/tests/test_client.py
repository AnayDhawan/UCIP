"""Client tests.

These run against a stubbed transport, not the network, so CI does not depend
on a deployment being up. What they pin is what is actually easy to get wrong:
URL and query construction, ward-code encoding, error translation, and the
frame shaping, which is the part this package exists for.

The live checks are in test_live.py and are skipped unless UCIP_LIVE is set.
"""

from __future__ import annotations

import json

import pytest
import requests

from ucip import (
    DEFAULT_BASE_URL,
    MissingDependency,
    Ucip,
    UcipError,
    UcipHTTPError,
    UcipNetworkError,
)


class FakeResponse:
    def __init__(self, payload, status=200, headers=None, text=None):
        self._payload = payload
        self.status_code = status
        self.headers = headers or {}
        self.url = "https://example.test"
        self.text = text if text is not None else json.dumps(payload)

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        if isinstance(self._payload, str):
            raise ValueError("not json")
        return self._payload


class FakeSession:
    """Records every call and replies with whatever it was primed with."""

    def __init__(self, response=None, error=None):
        self.headers = {}
        self.calls = []
        self._response = response
        self._error = error

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append({"url": url, "params": params or {}, "headers": headers})
        if self._error:
            raise self._error
        return self._response


def client(payload=None, **kwargs):
    session = FakeSession(FakeResponse(payload if payload is not None else {}, **kwargs))
    return Ucip(session=session), session


# ---------------------------------------------------------------- URL building


def test_defaults_to_the_public_deployment():
    assert Ucip().base_url == DEFAULT_BASE_URL


def test_strips_a_trailing_slash():
    assert Ucip("https://example.test/api/v1/").base_url == "https://example.test/api/v1"


def test_omits_parameters_that_were_not_given():
    api, session = client({"wards": []})
    api.wards()
    assert session.calls[0]["params"] == {}


def test_does_not_send_the_string_none():
    api, session = client({"cells": []})
    api.cells(ward=None, limit=5)
    assert session.calls[0]["params"] == {"limit": 5}


def test_booleans_go_over_the_wire_lowercase():
    # The API parses the literal string "true"; Python's str(True) is "True".
    api, session = client({"wards": []})
    api.wards(geometry=True)
    assert session.calls[0]["params"]["geometry"] == "true"

    api, session = client({"wards": []})
    api.wards(geometry=False)
    assert session.calls[0]["params"]["geometry"] == "false"


# ----------------------------------------------------------------- ward codes


def test_encodes_a_split_ward_code():
    # F/N is a real ward code and the slash breaks the path unencoded.
    api, session = client({"ward": {}})
    api.ward("F/N")
    assert session.calls[0]["url"] == f"{DEFAULT_BASE_URL}/wards/F%2FN"


def test_leaves_a_simple_code_alone():
    api, session = client({"ward": {}})
    api.ward("C")
    assert session.calls[0]["url"] == f"{DEFAULT_BASE_URL}/wards/C"


def test_trims_whitespace():
    api, session = client({"ward": {}})
    api.ward("  L  ")
    assert session.calls[0]["url"] == f"{DEFAULT_BASE_URL}/wards/L"


def test_rejects_an_empty_ward_code_without_a_request():
    api, session = client({})
    with pytest.raises(ValueError):
        api.ward("   ")
    assert session.calls == []


# --------------------------------------------------------------------- lookup


def test_lookup_sends_the_coordinate():
    api, session = client({"ward": {}})
    api.lookup(19.076, 72.877)
    assert session.calls[0]["params"] == {"lat": 19.076, "lon": 72.877}


@pytest.mark.parametrize("lat,lon", [(91, 0), (-91, 0), (0, 181), (0, -181)])
def test_lookup_refuses_out_of_range_coordinates(lat, lon):
    api, session = client({})
    with pytest.raises(ValueError):
        api.lookup(lat, lon)
    assert session.calls == []


def test_lookup_accepts_the_boundaries():
    # These are real coordinates, not errors.
    api, _ = client({"ward": {}})
    api.lookup(-90, -180)
    api.lookup(90, 180)


# --------------------------------------------------------------------- errors


def test_http_error_carries_the_apis_message_and_hint():
    api, _ = client(
        {"error": {"status": 404, "message": "No such ward.", "hint": "Try /wards."}},
        status=404,
    )
    with pytest.raises(UcipHTTPError) as caught:
        api.ward("ZZ")
    err = caught.value
    assert err.status == 404
    assert err.detail == "No such ward."
    assert err.hint == "Try /wards."
    assert err.is_rate_limited is False


def test_rate_limit_surfaces_retry_after_and_does_not_retry():
    api, session = client(
        {"error": {"status": 429, "message": "Too many requests."}},
        status=429,
        headers={"retry-after": "30"},
    )
    with pytest.raises(UcipHTTPError) as caught:
        api.wards()
    assert caught.value.is_rate_limited is True
    assert caught.value.retry_after == 30.0
    # One attempt. Retrying into a rate limiter makes it worse.
    assert len(session.calls) == 1


def test_survives_an_error_body_that_is_not_the_api_envelope():
    # An edge proxy returns HTML; failing to parse it must not replace a useful
    # 502 with a JSON decode error.
    api, _ = client("<html>502 Bad Gateway</html>", status=502, text="<html>502 Bad Gateway</html>")
    with pytest.raises(UcipHTTPError) as caught:
        api.meta()
    assert caught.value.status == 502
    assert caught.value.detail is None
    assert "502" in caught.value.body


def test_a_malformed_retry_after_is_ignored_rather_than_raising():
    api, _ = client({"error": {"status": 429}}, status=429, headers={"retry-after": "soon"})
    with pytest.raises(UcipHTTPError) as caught:
        api.wards()
    assert caught.value.retry_after is None


def test_transport_failure_becomes_a_network_error():
    api = Ucip(session=FakeSession(error=requests.ConnectionError("refused")))
    with pytest.raises(UcipNetworkError):
        api.meta()


def test_every_error_is_catchable_as_ucip_error():
    api, _ = client({"error": {"status": 400, "message": "bad"}}, status=400)
    with pytest.raises(UcipError):
        api.wards()


def test_missing_dependency_names_the_package(monkeypatch):
    """A broken environment should say which package, not raise from inside us.

    pandas is a hard dependency, so this only happens on a --no-deps install or
    a half-built environment. Simulated by making the lazy import fail.
    """
    import builtins

    real_import = builtins.__import__

    def explode(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("No module named 'pandas'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", explode)

    api, _ = client(WARDS)
    with pytest.raises(MissingDependency) as caught:
        api.wards_frame()
    message = str(caught.value)
    assert "pandas" in message
    assert "pip install" in message


def test_missing_dependency_is_also_an_import_error(monkeypatch):
    # So `except ImportError` around an optional import still behaves as a
    # reader would expect.
    assert issubclass(MissingDependency, ImportError)
    assert issubclass(MissingDependency, UcipError)


# --------------------------------------------------------------------- frames

WARDS = {
    "source": "database",
    "count": 2,
    "wards": [
        {
            "ward_id": "C",
            "hvi": 73.56,
            "rank": 1,
            "n_cells": 2,
            "contrib": {"LST_C": 0.22, "NDVI": 0.21},
            "dominant_factor": "LST_C",
            "dominant_share": 0.3,
            "single_factor_dominated": False,
        },
        {
            "ward_id": "F/N",
            "hvi": 57.76,
            "rank": 10,
            "n_cells": 13,
            "contrib": {"LST_C": 0.10, "NDVI": 0.06},
            "dominant_factor": "elderly_pct",
            "dominant_share": 0.28,
            "single_factor_dominated": False,
        },
    ],
}


def test_wards_frame_flattens_contrib_into_columns():
    # A column of dicts cannot be grouped, plotted or described, which is the
    # whole reason someone asked for a DataFrame.
    api, _ = client(WARDS)
    frame = api.wards_frame()
    assert "contrib" not in frame.columns
    assert frame.loc["C", "contrib_LST_C"] == 0.22
    assert frame.loc["F/N", "contrib_NDVI"] == 0.06


def test_wards_frame_is_indexed_by_ward_and_sorted_by_rank():
    api, _ = client(WARDS)
    frame = api.wards_frame()
    assert frame.index.name == "ward_id"
    assert list(frame.index) == ["C", "F/N"]
    assert list(frame["rank"]) == [1, 10]


def test_wards_frame_keeps_the_dominance_flag():
    # The #97 flag is the honesty signal on a score; dropping it in the frame
    # would hide exactly what a researcher needs to see.
    api, _ = client(WARDS)
    frame = api.wards_frame()
    assert "single_factor_dominated" in frame.columns
    assert "dominant_share" in frame.columns


def test_cells_frame_is_indexed_by_grid_id():
    api, session = client(
        {"source": "database", "count": 1, "cells": [{"grid_id": "cell_0000", "ward_id": "C", "hvi": 30.6}]}
    )
    frame = api.cells_frame()
    assert frame.index.name == "grid_id"
    assert frame.loc["cell_0000", "ward_id"] == "C"
    # One request at the endpoint ceiling, not a paging loop.
    assert session.calls[0]["params"]["limit"] == 1000


def test_recommendations_frame_keeps_the_citation():
    # A planting recommendation separated from the paper behind it is exactly
    # the artefact this project exists not to produce.
    api, _ = client(
        {
            "source": "database",
            "count": 1,
            "recommendations": [
                {
                    "ward_id": "C",
                    "intervention": "Cool roofs",
                    "rationale": "High vulnerability",
                    "citation": "Veldman et al. 2019, Science",
                    "priority": 1,
                    "cell_count": 7,
                }
            ],
        }
    )
    frame = api.recommendations_frame()
    assert frame.loc[0, "citation"] == "Veldman et al. 2019, Science"


def test_geo_frame_has_geometry_and_a_crs():
    api, _ = client(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [72.8, 19.0]},
                    "properties": {"ward_id": "C", "hvi": 73.5, "rank": 1},
                }
            ],
        }
    )
    frame = api.wards_geo()
    assert frame.crs == "EPSG:4326"
    assert frame.index.name == "ward_id"
    assert not frame.geometry.isna().any()


def test_geo_frame_asks_for_the_bulk_export():
    api, session = client(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [72.8, 19.0]},
                    "properties": {"grid_id": "cell_0000"},
                }
            ],
        }
    )
    api.cells_geo()
    assert session.calls[0]["url"].endswith("/export")
    assert session.calls[0]["params"] == {"dataset": "cells", "format": "geojson"}


def test_an_empty_export_is_an_error_rather_than_an_empty_frame():
    # An empty GeoDataFrame looks like a legitimate answer and would quietly
    # produce an empty map. A refresh that wrote nothing should be loud.
    api, _ = client({"type": "FeatureCollection", "features": []})
    with pytest.raises(UcipHTTPError):
        api.wards_geo()


def test_export_csv_requests_csv_and_returns_text():
    session = FakeSession(FakeResponse({}, text="ward_id,lon,lat\nC,72.8,19.0\n"))
    api = Ucip(session=session)
    csv = api.export_csv("wards")
    assert session.calls[0]["params"]["format"] == "csv"
    assert session.calls[0]["headers"]["accept"] == "text/csv"
    assert csv.splitlines()[0] == "ward_id,lon,lat"


def test_user_agent_is_sent_when_given():
    session = FakeSession(FakeResponse({}))
    Ucip(session=session, user_agent="my-tool/1.0").meta()
    assert session.headers["user-agent"] == "my-tool/1.0"
