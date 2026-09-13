"""Tests for the PEP 669 based dependency monitor."""

from __future__ import annotations

import importlib
import sys

import pytest

from conftest import make_project
from pytest_risktest.monitor import DependencyMonitor, MonitoringUnavailable, measure_overhead


@pytest.fixture()
def project(tmp_path):
    project_root = make_project(tmp_path)
    yield project_root
    # Each test builds the same module names in a different directory: drop the
    # cached modules so that a stale ``co_filename`` from a previous test cannot
    # leak into the next one.
    for name in [key for key in sys.modules if key == "app" or key.startswith("app.")]:
        sys.modules.pop(name, None)


def _import(root, name):
    sys.path.insert(0, str(root))
    try:
        return importlib.import_module(name)
    finally:
        sys.path.remove(str(root))


def test_monitoring_is_available_on_supported_interpreters():
    assert DependencyMonitor.available() is True


def test_records_files_executed_by_one_test(project):
    module = _import(project, "app.calc")
    monitor = DependencyMonitor(project, granularity="file")
    monitor.start_session()
    try:
        monitor.begin_test("tests/test_calc.py::test_add")
        module.add(2, 3)
        deps = monitor.end_test()
    finally:
        monitor.stop_session()

    assert "app/calc.py" in deps
    assert "app/text.py" not in deps
    assert deps["app/calc.py"] == set()


def test_dependencies_are_attributed_per_test(project):
    calc = _import(project, "app.calc")
    text = _import(project, "app.text")
    monitor = DependencyMonitor(project, granularity="file")
    monitor.start_session()
    try:
        monitor.begin_test("t1")
        calc.add(1, 1)
        first = monitor.end_test()
        monitor.begin_test("t2")
        text.shout("x")
        second = monitor.end_test()
    finally:
        monitor.stop_session()

    assert set(first) == {"app/calc.py"}
    assert set(second) == {"app/text.py"}


def test_files_outside_the_project_root_are_ignored(project, tmp_path):
    outside = tmp_path.parent / "outside_module.py"
    outside.write_text("def remote():\n    return 42\n", encoding="utf-8")
    sys.path.insert(0, str(outside.parent))
    try:
        module = importlib.import_module("outside_module")
        monitor = DependencyMonitor(project, granularity="file")
        monitor.start_session()
        try:
            monitor.begin_test("t")
            module.remote()
            deps = monitor.end_test()
        finally:
            monitor.stop_session()
    finally:
        sys.path.remove(str(outside.parent))
        sys.modules.pop("outside_module", None)
    assert deps == {}


def test_line_granularity_records_executed_lines(project):
    module = _import(project, "app.calc")
    monitor = DependencyMonitor(project, granularity="line")
    monitor.start_session()
    try:
        monitor.begin_test("t")
        assert module.add(1, 1) == 2
        assert module.is_even(4)
        deps = monitor.end_test()
    finally:
        monitor.stop_session()
    lines = deps["app/calc.py"]
    assert lines, "line granularity must record executed lines"
    assert all(isinstance(line, int) and line > 0 for line in lines)


def test_line_strategy_local_and_global_agree(project):
    module = _import(project, "app.calc")
    collected = {}
    for strategy in ("local", "global"):
        monitor = DependencyMonitor(project, granularity="line", line_strategy=strategy)
        monitor.start_session()
        try:
            monitor.begin_test("t")
            assert module.add(2, 2) == 4
            collected[strategy] = monitor.end_test()
        finally:
            monitor.stop_session()
    assert collected["local"] == collected["global"]
    assert collected["local"]["app/calc.py"]


def test_line_strategy_local_keeps_working_across_tests(project):
    module = _import(project, "app.calc")
    monitor = DependencyMonitor(project, granularity="line", line_strategy="local")
    monitor.start_session()
    try:
        monitor.begin_test("first")
        module.add(1, 1)
        first = monitor.end_test()
        monitor.begin_test("second")
        module.is_even(4)
        second = monitor.end_test()
    finally:
        monitor.stop_session()
    assert first.get("app/calc.py"), "first test lost its line data"
    assert second.get("app/calc.py"), "second test lost its line data"
    assert monitor._instrumented == set(), "local instrumentation must be released"


def test_line_events_do_not_leak_outside_a_test(project):
    module = _import(project, "app.calc")
    monitor = DependencyMonitor(project, granularity="line", line_strategy="local")
    monitor.start_session()
    try:
        monitor.begin_test("t")
        module.add(1, 1)
        monitor.end_test()
        monitor.begin_test("other")
        module.add(2, 2)
        after_idle_call = monitor.end_test()
    finally:
        monitor.stop_session()
    assert after_idle_call.get("app/calc.py") is not None


def test_unknown_line_strategy_is_rejected(project):
    with pytest.raises(ValueError):
        DependencyMonitor(project, granularity="line", line_strategy="bogus")


def test_no_events_are_collected_outside_a_test(project):
    module = _import(project, "app.calc")
    monitor = DependencyMonitor(project, granularity="file")
    monitor.start_session()
    try:
        module.add(5, 5)  # not attributed to any test
        monitor.begin_test("t")
        deps = monitor.end_test()
    finally:
        monitor.stop_session()
    assert deps == {}


def test_stop_session_is_idempotent(project):
    monitor = DependencyMonitor(project)
    monitor.start_session()
    monitor.stop_session()
    monitor.stop_session()
    assert monitor.stats["begin_test_calls"] == 0


def test_begin_and_end_test_without_session_is_safe(project):
    monitor = DependencyMonitor(project)
    monitor.begin_test("t")
    assert monitor.end_test() == {}


def test_measure_overhead_reports_percentage(project):
    module = _import(project, "app.calc")
    stats = measure_overhead(
        project,
        "file",
        lambda: [module.add(index, index) for index in range(50)],
    )
    assert stats["baseline_s"] > 0
    assert stats["traced_s"] >= 0
    assert stats["py_start_events"] > 0
    assert isinstance(stats["overhead_pct"], float)


def test_unavailable_monitor_raises_when_forced(monkeypatch, project):
    monkeypatch.setattr(DependencyMonitor, "available", staticmethod(lambda: False))
    monitor = DependencyMonitor(project)
    with pytest.raises(MonitoringUnavailable):
        monitor.start_session()
