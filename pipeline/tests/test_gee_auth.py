"""Tests for _gee_auth.py's env-var routing.

Needs the `ee` package (and, transitively, `cryptography`) to construct a real
credentials object, so this is skipped when only requirements-dev.txt is installed
(the lightweight "pipeline" CI job) and runs when the full pipeline/requirements.txt
stack is present. See pipeline/README.md.

Run:
    pip install -r requirements.txt
    pytest pipeline/tests/test_gee_auth.py
"""

import json
import sys
from pathlib import Path

import pytest

ee = pytest.importorskip("ee")
pytest.importorskip("cryptography")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _gee_auth  # noqa: E402


def _fake_rsa_key_pem() -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


@pytest.fixture
def fake_service_account_json() -> str:
    return json.dumps({
        "type": "service_account",
        "client_email": "svc@example.iam.gserviceaccount.com",
        "private_key": _fake_rsa_key_pem(),
        "private_key_id": "abc123",
        "token_uri": "https://oauth2.googleapis.com/token",
    })


@pytest.fixture
def captured_init_calls(monkeypatch):
    calls = []

    def fake_initialize(credentials="persistent", project=None):
        calls.append({"credentials": credentials, "project": project})

    monkeypatch.setattr(ee, "Initialize", fake_initialize)
    return calls


def test_no_env_vars_falls_back_to_plain_initialize(monkeypatch, captured_init_calls):
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_KEY_FILE", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    _gee_auth.init_ee("proj-x")

    assert captured_init_calls == [{"credentials": "persistent", "project": "proj-x"}]


def test_ambient_google_application_credentials_is_ignored(monkeypatch, captured_init_calls):
    """The bug this guards against: a dev with GOOGLE_APPLICATION_CREDENTIALS set for
    unrelated GCP tooling must NOT be silently routed into the service-account branch.
    """
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_KEY_FILE", raising=False)
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/nonexistent/ambient-cred.json")

    _gee_auth.init_ee("proj-x")

    # If the ambient var were picked up, this would raise FileNotFoundError trying to
    # open a path that doesn't exist. Reaching here with the plain fallback call proves
    # it wasn't.
    assert captured_init_calls == [{"credentials": "persistent", "project": "proj-x"}]


def test_service_account_json_env_var_used(monkeypatch, captured_init_calls, fake_service_account_json):
    monkeypatch.setenv("GEE_SERVICE_ACCOUNT_JSON", fake_service_account_json)
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_KEY_FILE", raising=False)

    _gee_auth.init_ee("proj-y")

    assert len(captured_init_calls) == 1
    assert captured_init_calls[0]["project"] == "proj-y"
    credentials = captured_init_calls[0]["credentials"]
    assert credentials != "persistent"
    assert credentials.service_account_email == "svc@example.iam.gserviceaccount.com"


def test_service_account_key_file_env_var_used(monkeypatch, tmp_path, captured_init_calls, fake_service_account_json):
    key_path = tmp_path / "key.json"
    key_path.write_text(fake_service_account_json, encoding="utf-8")

    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setenv("GEE_SERVICE_ACCOUNT_KEY_FILE", str(key_path))

    _gee_auth.init_ee("proj-z")

    assert len(captured_init_calls) == 1
    assert captured_init_calls[0]["project"] == "proj-z"
    assert captured_init_calls[0]["credentials"] != "persistent"


def test_missing_client_email_raises(monkeypatch):
    monkeypatch.setenv("GEE_SERVICE_ACCOUNT_JSON", json.dumps({"private_key": "x"}))
    monkeypatch.delenv("GEE_SERVICE_ACCOUNT_KEY_FILE", raising=False)

    with pytest.raises(ValueError, match="client_email"):
        _gee_auth.init_ee("proj-x")
