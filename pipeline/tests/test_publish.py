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
