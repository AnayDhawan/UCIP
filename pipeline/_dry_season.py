"""The dry-season composite window, as a pure calendar function.

Why this module exists: two callers need the same window and must not drift.

    02_gee_layers.py computes the Landsat composites for this window, so it has
    always owned the logic. run_pipeline.py now records the window a run was
    made from in data/pipeline_run_log.json, because the site's "how old is this
    data" story is only honest as a pair: *when* the pipeline last ran AND *what
    imagery* that run was computed from. Copying the calendar arithmetic into the
    orchestrator would let the two copies drift (different month constants, a
    different leap-year rule, ...), which is exactly the failure this repo
    extracts shared helpers to prevent (see _gee_auth.py and _publish.py).

    Importing this module has no side effects and needs no Earth Engine: both
    callers run it in environments where ee would be a heavy, sometimes
    unavailable, dependency (run_pipeline.py is imported by CI unit tests that
    never touch GEE), so the logic deliberately lives apart from 02's ee import.

    Mumbai's dry season runs November to February. Monsoon imagery is unusable
    for LST (cloud cover), so every composite in this pipeline is dry-season
    only, and the current and baseline windows must cover the same months to be
    comparable.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

DRY_START_MONTH = 11  # November
DRY_END_MONTH = 2  # February, of the following calendar year


def most_recent_complete_dry_season(today: date | None = None) -> tuple[str, str]:
    """The latest Nov-Feb window that has actually finished, as ISO date strings.

    The window used to be two hardcoded literals ("2025-11-01", "2026-02-28").
    That made the pipeline perfectly reproducible, which is genuinely useful, but
    it also made the monthly refresh in .github/workflows/pipeline-refresh.yml
    incapable of ever refreshing anything: re-running it re-fetched the same
    Landsat scenes and produced identical output, so the scheduled job would burn
    Earth Engine quota and open a pull request of float noise every month,
    forever. Confirmed on 2026-09-03 by running the full chain: every ward's HVI
    came back identical to 15 decimal places.

    Deriving the window from the calendar instead means a refresh run after
    February picks up the season that just ended, and a run before it keeps
    using the last complete one rather than averaging over a partial season.
    Composites are never built from a season still in progress, because a
    half-season mean is not comparable to a full-season baseline.

    Override with GEE_DRY_SEASON_END_YEAR to reproduce a specific past run.
    """
    today = today or date.today()
    # The season labelled Y ends in February of Y. It is complete once March of
    # that year has started.
    end_year = today.year if today.month > DRY_END_MONTH else today.year - 1
    override = os.environ.get("GEE_DRY_SEASON_END_YEAR")
    if override:
        end_year = int(override)
    start = date(end_year - 1, DRY_START_MONTH, 1)
    # Last day of February, leap years included.
    end = date(end_year, DRY_END_MONTH + 1, 1) - timedelta(days=1)
    return start.isoformat(), end.isoformat()
