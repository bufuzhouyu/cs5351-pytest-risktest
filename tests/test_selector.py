"""Tests for the selection and prioritisation engine."""

from __future__ import annotations

import pytest

from conftest import make_project
from pytest_risktest.config import POLICIES
from pytest_risktest.graph import ImportGraph
from pytest_risktest.selector import (
    order_tests,
    plan_selection,
    risk_score,
    git_changed_files,
    resolve_change,
)
from pytest_risktest.store import ChangeSet, Store

CALC_ADD = "tests/test_calc.py::test_add"
CALC_EVEN = "tests/test_calc.py::test_is_even"
TEXT = "tests/test_text.py::test_shout"
ALL = [CALC_ADD, CALC_EVEN, TEXT]


@pytest.fixture()
def world(tmp_path):
    make_project(tmp_path)
    store = Store(tmp_path / ".risktest" / "deps.sqlite3", tmp_path)
    store.refresh_digests(with_lines=True)
    store.record_test_dependencies(CALC_ADD, {"app/calc.py": {1, 2, 3}}, "fp-add")
    store.record_test_dependencies(CALC_EVEN, {"app/calc.py": {5, 6}}, "fp-even")
    store.record_test_dependencies(TEXT, {"app/text.py": {1, 2}}, "fp-text")
    graph = ImportGraph.from_root(tmp_path)
    yield store, graph, tmp_path
    store.close()


def _plan(store, graph, policy, change, **kwargs):
    kwargs.setdefault("min_selected", 0)
    kwargs.setdefault("max_deselect_pct", 100.0)
    return plan_selection(
        all_tests=ALL,
        store=store,
        graph=graph,
        policy=POLICIES[policy],
        change=change,
        **kwargs,
    )


def _change(*paths):
    return ChangeSet(changed=list(paths), added=[], removed=[], config_changed=[])


def test_policy_off_selects_everything(world):
    store, graph, _ = world
    plan = _plan(store, graph, "off", _change("app/calc.py"))
    assert plan.selected == ALL
    assert plan.deselected == []
    assert plan.reason_histogram() == {"policy-off": 3}


def test_fast_policy_selects_only_directly_exercised_tests(world):
    store, graph, _ = world
    plan = _plan(store, graph, "fast", _change("app/calc.py"))
    assert set(plan.selected) == {CALC_ADD, CALC_EVEN}
    assert plan.reasons[CALC_ADD] == "changed-dependency"
    assert TEXT in plan.deselected


def test_no_change_selects_nothing_when_stop_rule_is_disabled(world):
    store, graph, _ = world
    plan = _plan(store, graph, "balanced", ChangeSet([], [], [], []))
    assert plan.selected == []


def test_unknown_dependency_is_always_selected(world):
    store, graph, _ = world
    store.record_test_dependencies("tests/test_new.py::test_fresh", {}, "fp-new")
    plan = plan_selection(
        all_tests=[*ALL, "tests/test_new.py::test_fresh"],
        store=store,
        graph=graph,
        policy=POLICIES["balanced"],
        change=_change("app/calc.py"),
        min_selected=0,
        max_deselect_pct=100.0,
    )
    assert "tests/test_new.py::test_fresh" in plan.selected
    assert plan.reasons["tests/test_new.py::test_fresh"] in ("unknown-dependency", "new-test")


def test_previous_failure_and_flaky_tests_are_kept(world):
    store, graph, _ = world
    store.record_outcomes("run1", {CALC_ADD: "failed", CALC_EVEN: "passed", TEXT: "passed"},
                          {CALC_ADD: 0.1, CALC_EVEN: 0.1, TEXT: 0.1},
                          {CALC_ADD: "fp-add", CALC_EVEN: "fp-even", TEXT: "fp-text"})
    store.mark_flaky([TEXT])
    plan = _plan(store, graph, "fast", _change("app/calc.py"))
    assert plan.reasons[CALC_ADD] == "changed-dependency"
    assert TEXT in plan.selected
    assert plan.reasons[TEXT] == "flaky-suspect"


def test_forced_tests_are_selected(world):
    store, graph, _ = world
    plan = plan_selection(
        all_tests=ALL,
        store=store,
        graph=graph,
        policy=POLICIES["fast"],
        change=_change("app/calc.py"),
        forced=[TEXT],
        min_selected=0,
        max_deselect_pct=100.0,
    )
    assert plan.reasons[TEXT] == "always-run"


def test_transitive_policy_is_more_conservative_than_fast(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "low.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pkg" / "mid.py").write_text("from pkg.low import VALUE\n", encoding="utf-8")
    (tmp_path / "pkg" / "high.py").write_text("from pkg.mid import VALUE\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_high.py").write_text(
        "from pkg.high import VALUE\n\n\ndef test_value():\n    assert VALUE == 1\n",
        encoding="utf-8",
    )
    store = Store(tmp_path / ".risktest" / "deps.sqlite3", tmp_path)
    store.refresh_digests(with_lines=True)
    # The test only ever exercised pkg/high.py dynamically.
    store.record_test_dependencies("tests/test_high.py::test_value", {"pkg/high.py": set()}, "fp")
    graph = ImportGraph.from_root(tmp_path)
    try:
        fast = plan_selection(
            ["tests/test_high.py::test_value"], store, graph, POLICIES["fast"],
            _change("pkg/low.py"), min_selected=0, max_deselect_pct=100.0,
        )
        safe = plan_selection(
            ["tests/test_high.py::test_value"], store, graph, POLICIES["safe"],
            _change("pkg/low.py"), min_selected=0, max_deselect_pct=100.0,
        )
    finally:
        store.close()
    assert fast.selected == []
    assert safe.selected == ["tests/test_high.py::test_value"]
    assert safe.reasons["tests/test_high.py::test_value"] == "transitive-dependency"


def test_balanced_policy_uses_one_hop_closure(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "low.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pkg" / "mid.py").write_text("from pkg.low import VALUE\n", encoding="utf-8")
    (tmp_path / "pkg" / "high.py").write_text("from pkg.mid import VALUE\n", encoding="utf-8")
    store = Store(tmp_path / ".risktest" / "deps.sqlite3", tmp_path)
    store.refresh_digests()
    store.record_test_dependencies("t::a", {"pkg/mid.py": set()}, "fp")
    store.record_test_dependencies("t::b", {"pkg/high.py": set()}, "fp")
    graph = ImportGraph.from_root(tmp_path)
    try:
        plan = plan_selection(
            ["t::a", "t::b"], store, graph, POLICIES["balanced"],
            _change("pkg/low.py"), min_selected=0, max_deselect_pct=100.0,
        )
    finally:
        store.close()
    assert plan.selected == ["t::a"]


def test_line_granularity_marks_changed_lines(world):
    store, graph, _ = world
    plan = plan_selection(
        all_tests=ALL,
        store=store,
        graph=graph,
        policy=POLICIES["fast"],
        change=_change("app/calc.py"),
        granularity="line",
        changed_lines={"app/calc.py": {1, 2}},
        min_selected=0,
        max_deselect_pct=100.0,
    )
    assert plan.reasons[CALC_ADD] == "changed-line"
    assert plan.line_hits[CALC_ADD] == 2
    assert plan.reasons[CALC_EVEN] == "changed-dependency"


def test_configuration_change_forces_a_full_run(world):
    store, graph, _ = world
    change = ChangeSet([], [], [], ["pyproject.toml"])
    plan = _plan(store, graph, "fast", change)
    assert plan.fallback == "configuration files changed"
    assert plan.selected == ALL
    assert plan.deselected == []


def test_stop_rule_selects_a_minimum_share_of_the_suite(tmp_path):
    make_project(tmp_path)
    store = Store(tmp_path / ".risktest" / "deps.sqlite3", tmp_path)
    store.refresh_digests()
    tests = [f"t::test_{index}" for index in range(10)]
    for nodeid in tests:
        store.record_test_dependencies(nodeid, {"app/calc.py": set()}, "fp")
    graph = ImportGraph.from_root(tmp_path)
    try:
        plan = plan_selection(
            tests, store, graph, POLICIES["fast"], _change("app/text.py"),
            min_selected=1, max_deselect_pct=90.0,
        )
    finally:
        store.close()
    assert len(plan.selected) == 1


def test_min_selected_is_respected(world):
    store, graph, _ = world
    plan = plan_selection(
        ALL, store, graph, POLICIES["fast"], ChangeSet([], [], [], []),
        min_selected=2, max_deselect_pct=100.0,
    )
    assert len(plan.selected) == 2


def test_risk_score_prefers_recent_failures(world):
    store, _graph, _ = world
    store.record_outcomes("run1", {CALC_ADD: "failed", CALC_EVEN: "passed"},
                          {CALC_ADD: 0.1, CALC_EVEN: 0.1}, {CALC_ADD: "fp", CALC_EVEN: "fp"})
    states = store.test_states()
    assert risk_score(states[CALC_ADD], "changed-dependency", 0, 0) > risk_score(
        states[CALC_EVEN], "changed-dependency", 0, 0
    )
    assert risk_score(None, "changed-line", 5, 5) > risk_score(None, "transitive-dependency", 0, 0)


def test_selection_plan_serialisation(world):
    store, graph, _ = world
    plan = _plan(store, graph, "fast", _change("app/calc.py"))
    payload = plan.to_dict()
    assert payload["policy"] == "fast"
    assert payload["selected"] == 2
    assert payload["deselected"] == 1
    assert payload["skip_rate"] == pytest.approx(1 / 3, rel=1e-3)
    assert payload["changed_files"] == ["app/calc.py"]


def test_order_tests_supports_all_modes(world):
    store, graph, _ = world
    store.record_outcomes("run1", {TEXT: "failed"}, {TEXT: 0.1}, {TEXT: "fp"})
    plan = _plan(store, graph, "fast", _change("app/calc.py"))
    assert order_tests(plan, "original") == plan.selected
    shuffled = order_tests(plan, "shuffle", seed=7)
    assert sorted(shuffled) == sorted(plan.selected)
    assert order_tests(plan, "shuffle", seed=7) == shuffled
    risk_order = order_tests(plan, "risk")
    assert sorted(risk_order) == sorted(plan.selected)


def test_git_change_detection_returns_none_outside_a_repository(tmp_path):
    assert git_changed_files(tmp_path, "HEAD") is None


def test_resolve_change_mode_none_ignores_everything(world):
    store, _graph, _ = world
    change = resolve_change(
        store=store,
        root=store.root,
        mode="none",
        base_ref="HEAD",
        current_digests={"app/calc.py": "a"},
        previous_digests={"app/calc.py": "b"},
        previous_config={},
        current_config={},
    )
    assert change.is_empty is True

