"""Shared Earth Engine init helper used by every GEE-calling stage.

Why this exists:
    Every stage that talks to GEE (00, 02, 03, 06) called `ee.Initialize(project=...)`
    directly, which only works after an interactive `earthengine authenticate` has
    persisted user credentials to disk. That is fine for a developer's own machine but
    has no path to a headless environment such as a GitHub Actions runner (issue #58).

    This module centralizes Earth Engine initialization so a CI runner can authenticate
    with a service account (no browser, no interactive prompt) while a local developer's
    existing `earthengine authenticate` workflow keeps working unchanged: if no service
    account is configured, behavior is byte-for-byte what it was before this module
    existed.

Service-account credentials, when present, are read from one of these two
PIPELINE-SPECIFIC variables:
    GEE_SERVICE_ACCOUNT_JSON       the full key JSON as a string (e.g. a GitHub secret)
    GEE_SERVICE_ACCOUNT_KEY_FILE   a path to a key JSON file on disk (for local testing)

Deliberately NOT read: the ambient `GOOGLE_APPLICATION_CREDENTIALS` variable that
generic Google Cloud tooling (gcloud, other GCP client libraries) commonly sets. A
developer who has that exported for unrelated work would otherwise be silently
redirected off their working `earthengine authenticate` session into a service-account
branch that most likely has no Earth Engine access at all, producing a confusing
failure with nothing to do with what they actually touched. Requiring one of this
module's own, unambiguous variable names means the service-account path only ever
activates when someone deliberately set it up for this pipeline.

Neither variable is set in this fork/branch and no live GEE credentials were used to
test this path; see the PR description for what remains unverified.

Project-id resolution is also centralized here (resolve_project()) rather than left to
each stage's own `os.environ.get("GEE_PROJECT", "<default>")` line: before this module
existed, that line was copy-pasted into 00, 02, 03, and 06 with two different literal
defaults ("ucip-mumbai" in 00, matching .env.example; "ucip-mum", missing the second
syllable, in 02/03/06) that nobody had ever needed to reconcile, since 00 is a
standalone smoke test that never runs in the same process as the others. Now that
run_pipeline.py chains all of them in one CI job, and pipeline-refresh.yml's
GEE_PROJECT resolution step supports leaving the secret unset entirely (issue #58),
that drift became load-bearing: a run with no GEE_PROJECT secret configured would
authenticate stage 00 against "ucip-mumbai" and stages 02/03/06 against "ucip-mum" in
the same CI run. One shared resolve_project() means there is only one default left to
get right.
"""

from __future__ import annotations

import json
import os

import ee

# The project id every stage falls back to when GEE_PROJECT isn't set in the
# environment. Matches .env.example's documented GEE_PROJECT=ucip-mumbai.
DEFAULT_PROJECT = "ucip-mumbai"


def resolve_project() -> str:
    """The GEE project id to use: GEE_PROJECT from the environment if set, else
    DEFAULT_PROJECT. The single place this lookup happens, so every GEE-calling stage
    resolves to the same project by construction instead of by each stage's own
    copy-pasted os.environ.get(..., "<default>") agreeing (or not) with the others.
    """
    return os.environ.get("GEE_PROJECT", DEFAULT_PROJECT)


def init_ee(project: str | None = None) -> None:
    """Initialize Earth Engine, using a service account if one is configured.

    Falls back to the pre-existing `ee.Initialize(project=project)` behavior (relies on
    locally persisted `earthengine authenticate` credentials) when neither service
    account variable is set, so this is a strict superset of the previous behavior.

    `project` defaults to resolve_project() when not given explicitly, so a caller that
    just wants "the configured project" doesn't have to resolve it itself first.
    """
    if project is None:
        project = resolve_project()

    key_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
    key_path = os.environ.get("GEE_SERVICE_ACCOUNT_KEY_FILE")

    if key_json:
        info = json.loads(key_json)
        email = info.get("client_email")
        if not email:
            raise ValueError("GEE_SERVICE_ACCOUNT_JSON is missing 'client_email'")
        # key_data takes the JSON inline; no need to spill the secret to a temp file
        # on disk just to hand ee.ServiceAccountCredentials a path to read it back from.
        credentials = ee.ServiceAccountCredentials(email, key_data=key_json)
        ee.Initialize(credentials, project=project)
        return

    if key_path:
        with open(key_path, encoding="utf-8") as f:
            info = json.load(f)
        email = info.get("client_email")
        if not email:
            raise ValueError(f"{key_path} is missing 'client_email'")
        credentials = ee.ServiceAccountCredentials(email, key_file=key_path)
        ee.Initialize(credentials, project=project)
        return

    # Local-dev path, unchanged from before this module existed.
    ee.Initialize(project=project)
