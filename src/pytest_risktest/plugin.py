"""pytest integration.

The plugin is opt-in (``--risktest``).  Two responsibilities:

1. *Observer* -- trace which project files each test executes and persist the
   traces, so later runs can make decisions (works with ``--risktest-policy=off``
   too, which is how a baseline warm-up run is produced).
2. *Controller* -- select and order tests based on the fused evidence
   (:mod:`pytest_risktest.selector`).

A hard requirement is that the plugin can never turn a red suite green by
skipping the test that would have failed: every skip decision is justified by
evidence, and failures/flakiness/unseen tests are always selected
(``docs/05-evaluation-contract.md``, ``docs/06-risk-register.md``).
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set

import pytest

from .config import (
    CHANGE_MODES,
    DEFAULT_REPORT_PATH,
    DEFAULT_STORE_PATH,
    GRANULARITIES,
    LINE_STRATEGIES,
    ORDERINGS,
    POLICIES,
    RiskTestSettings,
    policy_from_name,
)
from .flaky import differential_findings
from .graph import ImportGraph
from .monitor import DependencyMonitor, MonitoringUnavailable
from .report import write_html, write_json, write_markdown
from .selector import SelectionPlan, order_tests, plan_selection, resolve_change
from .store import Store, dependency_fingerprint

MARKER_NAME = "risktest_always"
PLUGIN_NAME = "pytest-risktest-controller"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("risktest", "pytest-risktest: risk-aware test selection")
    group.addoption(
        "--risktest",
        action="store_true",
        default=False,
        help="enable risk-aware test selection, prioritisation and flakiness triage",
    )
    group.addoption(
        "--risktest-policy",
        choices=sorted(POLICIES),
        default="balanced",
        help="selection policy: off (trace only), fast, balanced (default) or safe",
    )
    group.addoption(
        "--risktest-granularity",
        choices=GRANULARITIES,
        default="file",
        help="dependency granularity (default: file)",
    )
    group.addoption(
        "--risktest-line-strategy",
        choices=LINE_STRATEGIES,
        default="local",
        help="line tracing strategy: local (per code object, default) or global",
    )
    group.addoption(
        "--risktest-order",
        choices=ORDERINGS,
        default="risk",
        help="ordering of the selected tests (default: risk)",
    )
    group.addoption(
        "--risktest-shuffle-seed",
        type=int,
        default=None,
        help="seed used by --risktest-order=shuffle (flakiness perturbation)",
    )
    group.addoption(
        "--risktest-changed",
        choices=CHANGE_MODES,
        default="auto",
        help="how changed files are detected (default: auto)",
    )
    group.addoption(
        "--risktest-base", default="HEAD", help="git revision used by --risktest-changed=git"
    )
    group.addoption(
        "--risktest-store", default=DEFAULT_STORE_PATH, help="dependency store location"
    )
    group.addoption(
        "--risktest-report",
        default=DEFAULT_REPORT_PATH,
        help="JSON report location ('' disables the report)",
    )
    group.addoption(
        "--risktest-max-deselect",
        type=float,
        default=90.0,
        help="stop rule: never deselect more than this percentage of the suite",
    )
    group.addoption(
        "--risktest-min-selected",
        type=int,
        default=1,
        help="stop rule: always execute at least this many tests",
    )
    group.addoption(
        "--risktest-trace-only",
        action="store_true",
        help="record dependencies but run every test",
    )
    group.addoption("--risktest-verbose", action="store_true", help="print extra diagnostics")
    parser.addini(
        "risktest_policy",
        "default pytest-risktest policy",
        default="",
    )


def pytest_configure(config: pytest.Config) -> None:
    try:
        enabled = bool(config.getoption("risktest"))
    except (ValueError, AttributeError):  # pragma: no cover - plugin loaded standalone
        return
    if not enabled:
        return
    settings = settings_from_config(config)
    controller = RiskTestController(config, settings)
    config.pluginmanager.register(controller, PLUGIN_NAME)


def settings_from_config(config: pytest.Config) -> RiskTestSettings:
    def option(name: str, default=None):
        try:
            return config.getoption(name)
        except (ValueError, AttributeError):
            return default

    policy_name = option("--risktest-policy") or config.getini("risktest_policy") or "balanced"
    report_path = option("--risktest-report", DEFAULT_REPORT_PATH)
    return RiskTestSettings(
        enabled=True,
        policy=policy_from_name(str(policy_name)),
        granularity=str(option("--risktest-granularity", "file")),
        line_strategy=str(option("--risktest-line-strategy", "local")),
        ordering=str(option("--risktest-order", "risk")),
        change_mode=str(option("--risktest-changed", "auto")),
        base_ref=str(option("--risktest-base", "HEAD")),
        store_path=str(option("--risktest-store", DEFAULT_STORE_PATH)),
        report_path=str(report_path) if report_path else None,
        shuffle_seed=option("--risktest-shuffle-seed"),
        max_deselect_pct=float(option("--risktest-max-deselect", 90.0)),
        min_selected=int(option("--risktest-min-selected", 1)),
        trace_only=bool(option("--risktest-trace-only", False)),
        verbose=bool(option("--risktest-verbose", False)),
    )


class RiskTestController:
    """Session-scoped pytest plugin implementing observation and selection."""

    def __init__(self, config: pytest.Config, settings: RiskTestSettings) -> None:
        self.config = config
        self.settings = settings
        self.root = Path(str(config.rootpath)).resolve()
        self.run_id = uuid.uuid4().hex[:12]
        self.store = Store(self._resolve(settings.store_path), self.root)
        self.monitor = DependencyMonitor(
            self.root, granularity=settings.granularity, line_strategy=settings.line_strategy
        )
        self.plan: Optional[SelectionPlan] = None
        self.graph: Optional[ImportGraph] = None
        self.digests: Dict[str, str] = {}
        self.dependencies: Dict[str, Dict[str, Set[int]]] = {}
        self.fingerprints: Dict[str, str] = {}
        self.outcomes: Dict[str, str] = {}
        self.durations: Dict[str, float] = {}
        self.flaky_findings: Dict[str, str] = {}
        self.last_report: Dict[str, object] = {}
        self.active_test: Optional[str] = None
        self.monitoring_active = False
        self.warnings: List[str] = []
        self.started_at = time.time()
        self._collect_started = time.perf_counter()
        self._collection_seconds = 0.0

    # ------------------------------------------------------------- utilities
    def _resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (self.root / path)

    # ---------------------------------------------------------------- header
    def pytest_report_header(self, config: pytest.Config) -> List[str]:
        settings = self.settings
        mode = "select" if settings.selecting else "trace-only"
        return [
            f"risktest: policy={settings.policy.name} ({mode}), "
            f"granularity={settings.granularity}/{settings.line_strategy}, order={settings.ordering}, "
            f"store={settings.store_path}"
        ]

    # ------------------------------------------------------------ collection
    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: List[pytest.Item]
    ) -> None:
        self._collection_seconds = time.perf_counter() - self._collect_started
        try:
            self._start_monitoring()
            nodeids = [item.nodeid for item in items]
            marked = self._apply_markers(items)
            previous_digests = self.store.file_digests("py")
            previous_config = self.store.file_digests("config")
            previous_line_hashes = self.store.line_hash_map()
            self.store.refresh_digests(with_lines=self.settings.granularity == "line")
            self.digests = self.store.file_digests("py")
            change = resolve_change(
                store=self.store,
                root=self.root,
                mode=self.settings.change_mode,
                base_ref=self.settings.base_ref,
                current_digests=self.digests,
                previous_digests=previous_digests,
                previous_config=previous_config,
                current_config=self.store.file_digests("config"),
            )
            self.store.prune_tests(nodeids)
            self.graph = ImportGraph.from_root(self.root)
            changed_lines = self._changed_lines(change.changed, previous_line_hashes)
            self.plan = plan_selection(
                all_tests=nodeids,
                store=self.store,
                graph=self.graph,
                policy=self.settings.policy,
                change=change,
                granularity=self.settings.granularity,
                changed_lines=changed_lines,
                max_deselect_pct=self.settings.max_deselect_pct,
                min_selected=self.settings.min_selected,
                forced=marked,
            )
            self._apply_selection(items)
        except MonitoringUnavailable as error:  # pragma: no cover - old interpreters
            self.warnings.append(str(error))
        except Exception as error:  # pragma: no cover - defensive: never break the suite
            self.warnings.append(f"risktest disabled after error: {error!r}")

    def _apply_markers(self, items: List[pytest.Item]) -> Set[str]:
        forced: Set[str] = set()
        for item in items:
            if item.get_closest_marker(MARKER_NAME) is not None:
                forced.add(item.nodeid)
                self.store.set_always_run(item.nodeid, True)
        return forced

    def _changed_lines(
        self, changed: List[str], previous_line_hashes: Dict[str, str]
    ) -> Dict[str, Set[int]]:
        if self.settings.granularity != "line":
            return {}
        result: Dict[str, Set[int]] = {}
        for path in changed:
            recorded = previous_line_hashes.get(path)
            if not recorded:
                continue
            try:
                text = (self.root / path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines = self.store.changed_lines_against(recorded, text)
            if lines:
                result[path] = lines
        return result

    def _apply_selection(self, items: List[pytest.Item]) -> None:
        plan = self.plan
        assert plan is not None
        if self.settings.selecting and plan.fallback is None:
            keep = set(plan.selected)
            deselected = [item for item in items if item.nodeid not in keep]
            selected_items = [item for item in items if item.nodeid in keep]
            if deselected:
                self.config.hook.pytest_deselected(items=deselected)
            items[:] = selected_items
        order = order_tests(plan, self.settings.ordering, self.settings.shuffle_seed)
        rank = {nodeid: index for index, nodeid in enumerate(order)}
        items.sort(key=lambda item: rank.get(item.nodeid, len(rank)))

    def _start_monitoring(self) -> None:
        if self.monitoring_active or not self.monitor.available():
            return
        self.monitor.start_session()
        self.monitoring_active = True

    # ---------------------------------------------------------------- tracing
    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        if not self.monitoring_active:
            return
        self.active_test = item.nodeid
        self.monitor.begin_test(item.nodeid)

    def pytest_runtest_teardown(self, item: pytest.Item, nextitem: Optional[pytest.Item]) -> None:
        if not self.monitoring_active or self.active_test is None:
            return
        deps = self.monitor.end_test()
        self.dependencies[item.nodeid] = deps
        self.active_test = None

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when == "call":
            self.outcomes[report.nodeid] = "failed" if report.failed else "passed"
        elif report.when == "setup" and report.failed:
            self.outcomes.setdefault(report.nodeid, "failed")
        elif report.when == "setup" and report.skipped:
            self.outcomes.setdefault(report.nodeid, "skipped")
        self.durations[report.nodeid] = self.durations.get(report.nodeid, 0.0) + report.duration

    # ------------------------------------------------------------- reporting
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        try:
            self._finalize_world()
        except Exception:  # pragma: no cover - reporting must never fail a run
            pass
        finally:
            if self.monitoring_active:
                self.monitor.stop_session()
                self.monitoring_active = False
            self.store.close()

    def _finalize_world(self) -> None:
        for nodeid, deps in self.dependencies.items():
            fingerprint = dependency_fingerprint(deps, self.digests)
            self.fingerprints[nodeid] = fingerprint
            self.store.record_test_dependencies(nodeid, deps, fingerprint)
        self.store.record_outcomes(
            self.run_id, self.outcomes, self.durations, self.fingerprints
        )
        findings = differential_findings(self.store, self.outcomes, self.fingerprints)
        if findings:
            self.store.mark_flaky(findings.keys(), True)
        self.flaky_findings = findings
        duration = time.time() - self.started_at
        failed = sum(1 for status in self.outcomes.values() if status == "failed")
        total = self.plan.total_tests if self.plan else len(self.outcomes)
        selected = self.plan.selected_count if self.plan else len(self.outcomes)
        self.store.record_run_summary(
            self.run_id,
            self.settings.policy.name,
            self.settings.granularity,
            selected,
            total,
            failed,
            duration,
        )
        self.last_report = self._build_report(duration, failed)
        if self.settings.report_path:
            target = self._resolve(self.settings.report_path)
            write_json(target, self.last_report)
            write_markdown(target.with_suffix(".md"), self.last_report)
            write_html(target.with_suffix(".html"), self.last_report)

    def _build_report(self, duration: float, failed: int) -> Dict[str, object]:
        plan = self.plan
        payload: Dict[str, object] = {
            "schema": 1,
            "run_id": self.run_id,
            "tool": "pytest-risktest",
            "timestamp": time.time(),
            "policy": self.settings.policy.name,
            "granularity": self.settings.granularity,
            "ordering": self.settings.ordering,
            "trace_only": not self.settings.selecting,
            "total_tests": plan.total_tests if plan else 0,
            "selected": plan.selected_count if plan else 0,
            "deselected": plan.deselected_count if plan else 0,
            "skip_rate": round(plan.skip_rate, 4) if plan else 0.0,
            "executed": len(self.outcomes),
            "failed": failed,
            "duration_s": round(duration, 4),
            "collection_s": round(self._collection_seconds, 4),
            "changed_files": plan.change.changed if plan else [],
            "added_files": plan.change.added if plan else [],
            "config_changed": plan.change.config_changed if plan else [],
            "fallback": plan.fallback if plan else None,
            "reason_histogram": plan.reason_histogram() if plan else {},
            "selected_tests": list(plan.selected) if plan else [],
            "deselected_tests": list(plan.deselected) if plan else [],
            "risk_scores": {k: v for k, v in (plan.risk.items() if plan else [])},
            "outcomes": dict(sorted(self.outcomes.items())),
            "durations": {k: round(v, 6) for k, v in sorted(self.durations.items())},
            "failures": sorted(k for k, v in self.outcomes.items() if v == "failed"),
            "flaky_findings": dict(sorted(self.flaky_findings.items())),
            "monitor": dict(self.monitor.stats),
            "store": self.store.summary(),
            "warnings": list(self.warnings),
        }
        return payload

    def pytest_terminal_summary(
        self, terminalreporter: "pytest.TerminalReporter", exitstatus: int, config: pytest.Config
    ) -> None:
        if not self.settings.verbose:
            return
        plan = self.plan
        if plan is None:
            return
        terminalreporter.write_sep("-", "pytest-risktest")
        terminalreporter.write_line(
            f"policy={plan.policy} tests={plan.total_tests} selected={plan.selected_count} "
            f"deselected={plan.deselected_count} skip_rate={plan.skip_rate:.1%}"
        )
        for reason, count in plan.reason_histogram().items():
            terminalreporter.write_line(f"  {reason}: {count}")
        if self.warnings:
            for warning in self.warnings:
                terminalreporter.write_line(f"  warning: {warning}")


@pytest.fixture
def risktest_store(request: pytest.FixtureRequest) -> Store:
    """Access the plugin's store from a test (used by the project's own tests)."""
    controller = request.config.pluginmanager.get_plugin(PLUGIN_NAME)
    if controller is None:  # pragma: no cover - only when the plugin is disabled
        pytest.skip("pytest-risktest is not enabled for this session")
    return controller.store


__all__ = ["pytest_addoption", "pytest_configure", "RiskTestController"]
