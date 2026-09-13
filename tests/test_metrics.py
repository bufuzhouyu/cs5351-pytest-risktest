"""Tests for the frozen evaluation metrics."""

from __future__ import annotations

import math

import pytest

from pytest_risktest.metrics import (
    aggregate_rows,
    apfd,
    missed_failures,
    overhead_pct,
    recall,
    skip_rate,
    summarize,
    time_saved,
)


def test_apfd_is_one_when_all_failures_come_first():
    # With m=2 faults among n=4 tests the theoretical maximum is 1 - m/(2n).
    order = ["f1", "f2", "p1", "p2"]
    assert apfd(order, {"f1", "f2"}) == pytest.approx(0.75)


def test_apfd_is_smallest_when_failures_come_last():
    order = ["p1", "p2", "f1", "f2"]
    assert apfd(order, {"f1", "f2"}) == pytest.approx(0.25)


def test_apfd_single_fault_is_one_when_detected_first():
    # Single fault detected by the very first test: 1 - 1/(2n) with n = 4.
    assert apfd(["f", "p1", "p2", "p3"], {"f"}) == pytest.approx(1 - 1 / 8)


def test_apfd_penalises_unselected_failing_tests():
    order = ["p1", "p2", "f1"]
    universe = ["p1", "p2", "f1", "f2"]
    assert apfd(order, {"f1", "f2"}, universe) < apfd(order, {"f1"}, universe)


def test_apfd_is_nan_without_failures():
    assert math.isnan(apfd(["a", "b"], set()))


def test_recall_and_missed_failures():
    assert recall(["a", "b"], ["b", "c"]) == pytest.approx(0.5)
    assert missed_failures(["a", "b"], ["b", "c"]) == ["c"]
    assert recall(["a"], []) == 1.0


def test_skip_rate():
    assert skip_rate(["a"], ["a", "b", "c"]) == pytest.approx(2 / 3)
    assert skip_rate([], []) == 0.0


def test_time_saved_and_overhead():
    assert time_saved(100.0, 25.0) == pytest.approx(0.75)
    assert overhead_pct(100.0, 105.0) == pytest.approx(5.0)
    assert math.isnan(time_saved(0.0, 1.0))


def test_summarize_and_aggregate_rows():
    stats = summarize([1.0, 2.0, 3.0])
    assert stats["n"] == 3
    assert stats["mean"] == pytest.approx(2.0)
    assert stats["median"] == pytest.approx(2.0)
    rows = [
        {"subject": "a", "policy": "fast", "recall": 1.0, "time_saved": 0.5},
        {"subject": "b", "policy": "fast", "recall": 0.9, "time_saved": 0.7},
    ]
    aggregated = aggregate_rows(rows)
    assert aggregated["recall"]["min"] == pytest.approx(0.9)
    assert aggregated["time_saved"]["max"] == pytest.approx(0.7)
    assert summarize([])["n"] == 0
