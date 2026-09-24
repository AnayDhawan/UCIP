"""Tests for _publish.py, the shared "copy to frontend/public/" helper used by
05_hvi.py, 06_nbs.py, 08_sensitivity.py, and 09_ndvi_change.py.

No third-party dependencies.

Run:
    pip install -r requirements-dev.txt
    pytest pipeline/tests/test_publish.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _publish import publish  # noqa: E402


def test_publish_copies_file_contents(tmp_path):
    src = tmp_path / "data" / "wards_hvi.geojson"
    src.parent.mkdir()
    src.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")

    dest = tmp_path / "public" / "wards_hvi.geojson"

    publish(src, dest)

    assert dest.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_publish_creates_missing_parent_directory(tmp_path):
    src = tmp_path / "src.json"
    src.write_text("{}", encoding="utf-8")

    dest = tmp_path / "does" / "not" / "exist" / "yet" / "dest.json"
    assert not dest.parent.exists()

    publish(src, dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "{}"


def test_publish_overwrites_existing_dest(tmp_path):
    src = tmp_path / "src.json"
    src.write_text("new content", encoding="utf-8")

    dest = tmp_path / "dest.json"
    dest.write_text("stale content", encoding="utf-8")

    publish(src, dest)

    assert dest.read_text(encoding="utf-8") == "new content"


def test_publish_prints_confirmation(tmp_path, capsys):
    src = tmp_path / "src.json"
    src.write_text("{}", encoding="utf-8")
    dest = tmp_path / "dest.json"

    publish(src, dest)

    out = capsys.readouterr().out
    assert "[ok] copied" in out
    assert str(dest) in out


class TestPublishGuard:
    """Only the published configuration may write to frontend/public/ (issue #96).

    CityConfig.publishes_to_frontend existed for this and only stages 14 and 15
    consulted it. The other seven called publish() unconditionally, so a Pune
    run would have replaced Mumbai's live snapshots, and a 500 m run did
    replace them. The guard is inside publish() now, because a guard every
    caller has to remember is one that a caller will forget.
    """

    def city(self, slug="mumbai", cell_size_m=1000.0):
        from dataclasses import replace

        import _city

        return replace(_city.load_city("mumbai"), slug=slug, cell_size_m=cell_size_m)

    def paths(self, tmp_path):
        src = tmp_path / "data" / "wards_hvi.geojson"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")
        return src, tmp_path / "public" / "wards_hvi.geojson"

    def test_the_published_configuration_still_publishes(self, tmp_path):
        src, dest = self.paths(tmp_path)
        assert publish(src, dest, self.city()) is True
        assert dest.exists()

    def test_a_second_city_does_not_touch_the_live_snapshots(self, tmp_path):
        src, dest = self.paths(tmp_path)
        assert publish(src, dest, self.city(slug="pune")) is False
        assert not dest.exists()

    def test_a_non_default_resolution_does_not_touch_them_either(self, tmp_path):
        src, dest = self.paths(tmp_path)
        assert publish(src, dest, self.city(cell_size_m=500.0)) is False
        assert not dest.exists()

    def test_it_refuses_rather_than_overwriting_an_existing_file(self, tmp_path):
        # The failure that actually happened: the destination already held the
        # published 1 km dataset and a 500 m run wrote over it.
        src, dest = self.paths(tmp_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("the published dataset", encoding="utf-8")

        assert publish(src, dest, self.city(cell_size_m=500.0)) is False
        assert dest.read_text(encoding="utf-8") == "the published dataset"

    def test_it_says_why_it_skipped(self, tmp_path, capsys):
        # "Why is the dashboard unchanged" is a question the log should answer.
        src, dest = self.paths(tmp_path)
        publish(src, dest, self.city(cell_size_m=500.0))
        out = capsys.readouterr().out
        assert "not publishing" in out
        assert "500m" in out
