"""Regression tests for the selection policies, ordering and metrics.

These tests complement ``tests/test_selector.py`` and ``tests/test_metrics.py``
by pinning the small, documented contracts that the benchmark and the report
depend on:

* each named policy maps onto exactly one point of the recall/precision curve;
* ordering keeps the selection intact and only changes the order;
* a failure that was never executed must score worse than one that ran last;
* every metric guards its degenerate inputs with ``NaN`` or ``0.0`` instead of
  raising, because the benchmark aggregates over runs that can be empty.

Every test checks one behaviour only, so a regression points at a single
contract.
"""

from __future__ import annotations

import math

import pytest

from pytest_risktest.config import POLICIES, policy_from_name
from pytest_risktest.metrics import (
    apfd,
    missed_failures,
    overhead_pct,
    recall,
    skip_rate,
    summarize,
    time_saved,
)
from pytest_risktest.selector import SelectionPlan, order_tests
from pytest_risktest.store import ChangeSet


# --------------------------------------------------------------------- policies
def test_fast_policy_has_no_static_closure():
    assert POLICIES["fast"].transitive_depth == 0


def test_safe_policy_uses_full_closure():
    assert POLICIES["safe"].transitive_depth is None


def test_balanced_policy_uses_exactly_one_hop():
    assert POLICIES["balanced"].transitive_depth == 1


@pytest.mark.parametrize(
    ("policy_name", "expected_label"),
    [("off", "0"), ("fast", "0"), ("balanced", "1"), ("safe", "closure")],
)
def test_depth_label_describes_the_policy(policy_name, expected_label):
    assert POLICIES[policy_name].depth_label == expected_label


def test_policy_from_name_round_trips_and_rejects_unknown_names():
    assert policy_from_name("fast") is POLICIES["fast"]
    with pytest.raises(ValueError):
        policy_from_name("turbo")


# ---------------------------------------------------------------------- metrics
def test_apfd_rewards_detecting_the_failure_first():
    assert apfd(["f", "p1", "p2", "p3"], {"f"}) == pytest.approx(0.875)


def test_apfd_is_nan_without_failures():
    assert math.isnan(apfd(["a", "b"], set()))


def test_apfd_penalises_a_failure_that_was_never_executed():
    """An unexecuted failure must score below the same failure found last."""
    universe = ["a", "b", "c"]
    executed_last = apfd(["a", "b"], {"b"}, universe=universe)
    never_executed = apfd(["a", "b"], {"c"}, universe=universe)
    assert never_executed < executed_last


def test_recall_counts_a_missed_failure():
    assert recall(["a", "b"], ["b", "c"]) == pytest.approx(0.5)


def test_recall_is_one_when_nothing_failed():
    assert recall([], []) == pytest.approx(1.0)
    assert recall(["a"], []) == pytest.approx(1.0)


def test_missed_failures_lists_unexecuted_tests_in_sorted_order():
    assert missed_failures(["a"], {"c", "b", "a"}) == ["b", "c"]
    assert missed_failures(["a", "b", "c"], {"a", "b", "c"}) == []


def test_skip_rate_handles_empty_and_partial_selections():
    assert skip_rate([], []) == pytest.approx(0.0)
    assert skip_rate(["a"], ["a", "b"]) == pytest.approx(0.5)
    assert skip_rate(["a", "b"], ["a", "b"]) == pytest.approx(0.0)


def test_time_saved_reports_the_fraction_and_guards_zero_duration():
    assert time_saved(10, 4) == pytest.approx(0.6)
    assert time_saved(10, 10) == pytest.approx(0.0)
    assert math.isnan(time_saved(0, 1))


def test_overhead_pct_reports_relative_cost_and_guards_zero_baseline():
    assert overhead_pct(100, 150) == pytest.approx(50.0)
    assert overhead_pct(100, 100) == pytest.approx(0.0)
    assert math.isnan(overhead_pct(0, 5))


def test_summarize_reports_basic_statistics():
    stats = summarize([1, 2, 3])
    assert stats["n"] == 3
    assert stats["mean"] == pytest.approx(2.0)
    assert stats["median"] == pytest.approx(2.0)
    assert stats["min"] == pytest.approx(1.0)
    assert stats["max"] == pytest.approx(3.0)


def test_summarize_drops_nan_and_handles_empty_input():
    stats = summarize([1.0, float("nan"), 3.0])
    assert stats["n"] == 2
    assert stats["mean"] == pytest.approx(2.0)

    empty = summarize([])
    assert empty["n"] == 0
    assert math.isnan(empty["mean"])


# ---------------------------------------------------------------------- ordering
def _plan(selected, risk):
    return SelectionPlan(
        policy="fast",
        granularity="file",
        total_tests=len(selected),
        selected=list(selected),
        deselected=[],
        reasons={},
        risk=dict(risk),
        change=ChangeSet([], [], [], []),
    )


def test_order_tests_original_preserves_the_plan_order():
    plan = _plan(["a", "b", "c"], {"a": 1.0, "b": 2.0, "c": 0.5})
    assert order_tests(plan, "original") == ["a", "b", "c"]


def test_order_tests_risk_sorts_by_descending_score():
    plan = _plan(["a", "b", "c"], {"a": 1.0, "b": 2.0, "c": 0.5})
    assert order_tests(plan, "risk") == ["b", "a", "c"]


def test_order_tests_shuffle_is_reproducible_and_keeps_the_selection():
    plan = _plan(["a", "b", "c", "d"], {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0})
    first = order_tests(plan, "shuffle", seed=7)
    second = order_tests(plan, "shuffle", seed=7)
    assert first == second
    assert sorted(first) == sorted(plan.selected)
