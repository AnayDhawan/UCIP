"""Tests for schema validation of city configs (issue #107).

The point of validating in CI is that a malformed config fails in seconds
rather than forty minutes into an Earth Engine run that then writes half a
dataset. These tests break a config on purpose, one field at a time, and check
the failure names the field. An error that says "config is invalid" would pass
a test that only asserted failure, and would not help anyone.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

import validate_cities  # noqa: E402

ROOT = PIPELINE_DIR.parent
SCHEMA = json.loads((ROOT / "config" / "city.schema.json").read_text(encoding="utf-8"))
MUMBAI = json.loads((ROOT / "config" / "cities" / "mumbai.json").read_text(encoding="utf-8"))


def errors_for(cfg: dict) -> list[str]:
    found: list[str] = []
    validate_cities.check_schema(cfg, SCHEMA, found, "test.json")
    return found


def test_the_real_config_is_valid():
    assert errors_for(MUMBAI) == []


def test_a_missing_required_key_names_it():
    cfg = {k: v for k, v in MUMBAI.items() if k != "bbox"}
    found = errors_for(cfg)
    assert found
    assert any("bbox" in e for e in found)


def test_a_wrong_type_is_caught_and_named():
    """The hand-rolled check this replaced only looked for absent keys, so a
    bbox that was a string passed validation and blew up in the pipeline."""
    cfg = {**MUMBAI, "bbox": "72.7,18.8,73.0,19.3"}
    found = errors_for(cfg)
    assert found
    assert any(e.startswith("test.json: bbox:") for e in found)


def test_a_bbox_of_the_wrong_length_is_caught():
    cfg = {**MUMBAI, "bbox": [72.7, 18.8, 73.0]}
    found = errors_for(cfg)
    assert found
    assert any("bbox" in e for e in found)


def test_an_unknown_key_is_rejected():
    """additionalProperties is false in the schema, so a typo is an error
    rather than a silently ignored field."""
    cfg = {**MUMBAI, "projected_crs": "EPSG:32643"}
    found = errors_for(cfg)
    assert found
    assert any("projected_crs" in e for e in found)


def test_a_nested_field_error_reports_its_path():
    cfg = json.loads(json.dumps(MUMBAI))
    cfg["grid"]["cell_size_m"] = "1000"
    found = errors_for(cfg)
    assert found
    assert any(e.startswith("test.json: grid.cell_size_m:") for e in found)


def test_every_error_is_reported_not_just_the_first():
    cfg = json.loads(json.dumps(MUMBAI))
    cfg["bbox"] = "nope"
    cfg["grid"]["cell_size_m"] = "1000"
    found = errors_for(cfg)
    assert len(found) >= 2


def test_the_schema_itself_is_valid():
    """A broken schema would otherwise pass everything silently."""
    import jsonschema

    validator_cls = jsonschema.validators.validator_for(SCHEMA)
    validator_cls.check_schema(SCHEMA)


def test_the_validator_matches_the_schema_draft():
    """city.schema.json declares draft 2020-12. jsonschema 3.x has no validator
    for it and silently falls back to draft 7, which drops prefixItems and stops
    checking that the bbox is four numbers. Pin the expectation here so an
    accidental downgrade fails a test rather than quietly weakening validation.
    """
    import jsonschema

    validator_cls = jsonschema.validators.validator_for(SCHEMA)
    assert validator_cls is jsonschema.Draft202012Validator


@pytest.mark.parametrize("slug", ["mumbai", "pune"])
def test_shipped_configs_validate(slug):
    cfg = json.loads((ROOT / "config" / "cities" / f"{slug}.json").read_text(encoding="utf-8"))
    assert errors_for(cfg) == []
