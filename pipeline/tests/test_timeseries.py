"""Tests for the multi-year trend fitting in 14_timeseries.py (issue #64).

The significance testing is what these lock down. Without it the stage reported
24 of 24 Mumbai wards "cooling at 1 C per decade" from a record whose
year-to-year scatter is larger than the trend being claimed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))


@pytest.fixture(scope="module")
def ts():
    spec = importlib.util.spec_from_file_location("ts", PIPELINE_DIR / "14_timeseries.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestLinearFit:
    def test_recovers_a_clean_slope(self, ts):
        xs = [float(y) for y in range(2014, 2027)]
        ys = [10 + 0.5 * (x - 2014) for x in xs]
        fit = ts.linear_fit(xs, ys)
        assert fit["slope"] == pytest.approx(0.5)
        assert fit["r_squared"] == pytest.approx(1.0)

    def test_a_perfect_fit_is_significant(self, ts):
        xs = [float(y) for y in range(2014, 2027)]
        ys = [10 + 0.5 * (x - 2014) for x in xs]
        assert ts.linear_fit(xs, ys)["p_value"] < 0.05

    def test_flat_data_has_zero_slope(self, ts):
        xs = [float(y) for y in range(2014, 2027)]
        fit = ts.linear_fit(xs, [30.0] * len(xs))
        assert fit["slope"] == pytest.approx(0.0)

    def test_noise_alone_is_not_significant(self, ts):
        # Alternating values with no trend. A naive slope-only implementation
        # would still report some non-zero number here and call it a direction.
        xs = [float(y) for y in range(2014, 2027)]
        ys = [30.0 + (2.0 if i % 2 else -2.0) for i in range(len(xs))]
        fit = ts.linear_fit(xs, ys)
        assert fit["p_value"] > 0.05

    def test_reports_standard_error_and_r_squared(self, ts):
        xs = [float(y) for y in range(2014, 2027)]
        ys = [30.0 + (1.5 if i % 3 else -1.5) for i in range(len(xs))]
        fit = ts.linear_fit(xs, ys)
        assert fit["stderr"] is not None and fit["stderr"] > 0
        assert 0.0 <= fit["r_squared"] <= 1.0

    def test_too_few_points_returns_no_fit(self, ts):
        fit = ts.linear_fit([2014.0, 2015.0], [30.0, 31.0])
        assert fit["p_value"] is None


class TestClassify:
    def _fit(self, slope_per_year, p):
        return {"slope": slope_per_year, "p_value": p, "stderr": 0.1, "r_squared": 0.9, "n": 13}

    def test_significant_warming_is_reported(self, ts):
        label = ts.classify(self._fit(0.05, 0.01), self._fit(0.0, 0.9))
        assert "warming" in label

    def test_significant_cooling_is_reported(self, ts):
        label = ts.classify(self._fit(-0.05, 0.01), self._fit(0.0, 0.9))
        assert "cooling" in label

    def test_large_but_insignificant_slope_claims_nothing(self, ts):
        # The exact case that produced the false Mumbai result: a big slope with
        # a p-value nowhere near significance.
        label = ts.classify(self._fit(-0.10, 0.18), self._fit(0.0, 0.9))
        assert "no detected temperature trend" in label
        assert "cooling" not in label

    def test_significant_but_tiny_slope_claims_nothing(self, ts):
        # Statistically detectable and practically meaningless.
        label = ts.classify(self._fit(0.001, 0.001), self._fit(0.0, 0.9))
        assert "no detected temperature trend" in label

    def test_vegetation_is_classified_independently(self, ts):
        label = ts.classify(self._fit(0.0, 0.9), self._fit(0.005, 0.01))
        assert "greening" in label
