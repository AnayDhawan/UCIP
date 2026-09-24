"""Checks against the live deployment.

Skipped unless UCIP_LIVE is set. CI should not fail because a deployment is
down, but a client whose only tests use a stub it also wrote has proven nothing
about the API it claims to speak to. Run before publishing:

    UCIP_LIVE=1 python -m pytest tests/
"""

from __future__ import annotations

import os

import pytest

from ucip import Ucip, UcipHTTPError

pytestmark = pytest.mark.skipif(
    not os.environ.get("UCIP_LIVE"), reason="set UCIP_LIVE=1 to run against the deployment"
)


@pytest.fixture(scope="module")
def api() -> Ucip:
    return Ucip(user_agent="ucip-python-tests")


def test_the_three_line_path(api):
    """The acceptance criterion for issue #104, exactly as written."""
    wards = api.wards_geo()
    assert len(wards) == 24
    assert wards.crs == "EPSG:4326"
    assert not wards.geometry.isna().any()
    assert wards.geometry.is_valid.all()


def test_the_geo_frame_and_the_plain_frame_agree_on_column_names(api):
    """Found by installing the package and running the three-line path.

    `wards_geo()` is built on /export and `wards_frame()` on /wards, and the
    export used to publish the pipeline's own spelling: the GeoDataFrame had
    `HVI` where the DataFrame had `hvi`. Two methods of one client disagreeing
    about the name of the column carrying the score is not a difference anyone
    should have to discover.
    """
    geo = api.wards_geo()
    frame = api.wards_frame()

    shared = {"hvi", "rank", "n_cells", "dominant_factor", "single_factor_dominated"}
    assert shared <= set(geo.columns), f"missing from wards_geo: {shared - set(geo.columns)}"
    assert shared <= set(frame.columns), f"missing from wards_frame: {shared - set(frame.columns)}"

    # No SCREAMING leftovers from the snapshot on either path.
    for screaming in ("HVI", "LST_C", "NDVI", "NDVI_prev"):
        assert screaming not in geo.columns
        assert screaming not in frame.columns

    # And the values agree, not just the names.
    assert geo.loc["C", "hvi"] == pytest.approx(frame.loc["C", "hvi"])


def test_cells_geo_uses_the_published_names(api):
    cells = api.cells_geo()
    assert {"hvi", "lst_c", "ndvi"} <= set(cells.columns)
    for screaming in ("HVI", "LST_C", "NDVI", "NDVI_prev"):
        assert screaming not in cells.columns


def test_wards_frame_is_ranked_and_decomposed(api):
    frame = api.wards_frame()
    assert len(frame) == 24
    assert list(frame["rank"]) == sorted(frame["rank"])
    # The explainability claim: a score decomposes into its drivers.
    contrib = [c for c in frame.columns if c.startswith("contrib_")]
    assert len(contrib) == 8


def test_cells_frame_covers_the_whole_grid(api):
    frame = api.cells_frame()
    assert len(frame) > 500
    assert frame["ward_id"].nunique() == 24


def test_recommendations_all_carry_a_citation(api):
    frame = api.recommendations_frame()
    assert len(frame) > 0
    assert frame["citation"].str.strip().ne("").all()


def test_split_ward_code_over_the_wire(api):
    assert api.ward("F/N")["ward"]["ward_id"] == "F/N"


def test_lookup_resolves_a_real_coordinate(api):
    assert api.lookup(19.076, 72.877)["ward"]["ward_id"] == "L"


def test_lookup_404s_outside_every_ward(api):
    with pytest.raises(UcipHTTPError) as caught:
        api.lookup(0, 0)
    assert caught.value.status == 404


def test_meta_reports_coverage(api):
    meta = api.meta()
    assert meta["counts"]["wards"] == 24
    assert meta["license"]["code"] == "Apache-2.0"


def test_csv_export_has_coordinate_columns(api):
    header = api.export_csv("wards").splitlines()[0].split(",")
    # So the CSV is usable without a geometry library at all.
    assert "lon" in header and "lat" in header


def test_the_generated_models_match_the_live_response(api):
    """Every key the API returns is one the generated models declare.

    The generated TypedDicts come from a committed spec artifact. This is the
    check that the artifact still matches the deployment, which no amount of
    regenerating locally can tell you.
    """
    from ucip.models import Ward

    declared = set(Ward.__annotations__)
    for ward in api.wards()["wards"]:
        undocumented = set(ward) - declared
        assert not undocumented, f"live API returned undeclared ward fields: {undocumented}"
