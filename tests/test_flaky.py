"""Tests for flakiness triage."""

from __future__ import annotations

from pytest_risktest.flaky import (
    CONSISTENT_FAIL,
    CONSISTENT_PASS,
    NONDETERMINISTIC,
    ORDER_DEPENDENT,
    UNKNOWN,
    classify_pair,
    differential_findings,
    flaky_candidates,
    suspects_from_verdicts,
    summarize,
)
from pytest_risktest.store import Store


def test_classify_pair_labels_every_case():
    first = {"a": "passed", "b": "failed", "c": "passed", "d": "failed"}
    second = {"a": "passed", "b": "failed", "c": "failed", "d": "passed", "e": "passed"}
    verdicts = classify_pair(first, second)
    assert verdicts["a"] == CONSISTENT_PASS
    assert verdicts["b"] == CONSISTENT_FAIL
    assert verdicts["c"] == ORDER_DEPENDENT
    assert verdicts["d"] == ORDER_DEPENDENT
    assert verdicts["e"] == UNKNOWN


def test_identical_fingerprints_assume_order_dependence():
    verdicts = classify_pair({"a": "passed"}, {"a": "failed"}, fingerprints_match=True)
    assert verdicts["a"] == ORDER_DEPENDENT
    verdicts = classify_pair({"a": "passed"}, {"a": "failed"}, fingerprints_match=False)
    assert verdicts["a"] == NONDETERMINISTIC


def test_differential_findings_detects_contradicting_history(tmp_path):
    store = Store(tmp_path / "s.sqlite3", tmp_path)
    try:
        store.record_outcomes("run1", {"t": "passed"}, {"t": 0.1}, {"t": "fp"})
        findings = differential_findings(store, {"t": "failed"}, {"t": "fp"})
        assert findings == {"t": NONDETERMINISTIC}
        same = differential_findings(store, {"t": "passed"}, {"t": "fp"})
        assert same == {}
    finally:
        store.close()


def test_tests_without_fingerprint_are_not_judged(tmp_path):
    store = Store(tmp_path / "s.sqlite3", tmp_path)
    try:
        store.record_outcomes("run1", {"t": "passed"}, {"t": 0.1}, {"t": "fp"})
        assert differential_findings(store, {"t": "failed"}, {}) == {}
    finally:
        store.close()


def test_flaky_candidates_and_summaries(tmp_path):
    store = Store(tmp_path / "s.sqlite3", tmp_path)
    try:
        store.record_outcomes("run1", {"a": "passed", "b": "passed"}, {"a": 0.1, "b": 0.1},
                              {"a": "fp", "b": "fp"})
        store.mark_flaky(["a"])
        assert flaky_candidates(store) == ["a"]
    finally:
        store.close()
    assert summarize([CONSISTENT_PASS, CONSISTENT_PASS, ORDER_DEPENDENT]) == {
        CONSISTENT_PASS: 2,
        ORDER_DEPENDENT: 1,
    }
    assert suspects_from_verdicts({"a": CONSISTENT_PASS, "b": ORDER_DEPENDENT}) == ["b"]


def test_different_dependency_fingerprint_is_not_flaky(tmp_path):
    store = Store(tmp_path / "s.sqlite3", tmp_path)
    try:
        store.record_outcomes("run1", {"t": "passed"}, {"t": 0.1}, {"t": "old"})
        assert differential_findings(store, {"t": "failed"}, {"t": "new"}) == {}
        assert differential_findings(store, {"t": "failed"}, {"t": "old"}) == {
            "t": NONDETERMINISTIC
        }
    finally:
        store.close()