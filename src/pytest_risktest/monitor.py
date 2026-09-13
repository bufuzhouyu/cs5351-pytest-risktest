"""Dynamic per-test dependency collection built on PEP 669 (``sys.monitoring``).

Why PEP 669 instead of ``sys.settrace``?
----------------------------------------
The classical way to collect test dependencies is a full tracer (``sys.settrace``
or ``coverage.Coverage``).  A tracer pays a Python-level callback for *every*
executed line, which inflates the runtime of the observed suite and distorts the
measurements the tool itself is supposed to report.

PEP 669 ("low impact monitoring", CPython 3.12+) allows a tool to subscribe to a
small event set, so the interpreter only pays for the events the tool asked for.
``pytest-risktest`` subscribes to ``PY_START`` (cheap, function-entry level) and
optionally to ``LINE`` (more precise, more expensive).

Two line-tracing strategies are implemented, because the naive one turned out to
be impractical during the evaluation:

``global``
    ``LINE`` is enabled for the whole interpreter.  Every executed line of every
    module -- including pytest itself and third-party libraries -- pays a callback.

``local`` (default)
    ``LINE`` is enabled lazily *per code object* from the ``PY_START`` callback,
    which then returns :data:`sys.monitoring.DISABLE` so that object never pays
    the (now redundant) function-entry event again.  Code objects outside the
    project, and code executed outside a test, never pay for line events.
    ``benchmark/experiments/tracing_strategies.py`` measures both.

``PY_START`` also gives the cheaper *file* granularity: a tight loop inside one
function costs one callback instead of one per iteration, which is why it is the
default and why its measured overhead is close to zero.

The monitor never raises into user code: a broken observer must not break the
test suite it observes (NFR-2 in ``docs/03-requirements.md``).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional, Set

EXCLUDED_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".risktest",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "build",
        "dist",
        "site-packages",
    }
)

_TOOL_ID_CANDIDATES = ("PROFILER_ID", "COVERAGE_ID", "DEBUGGER_ID", "OPTIMIZER_ID")


class MonitoringUnavailable(RuntimeError):
    """Raised when the running interpreter cannot provide PEP 669 monitoring."""


class DependencyMonitor:
    """Collects ``test -> {file: {lines}}`` observations for one pytest session.

    Usage::

        monitor = DependencyMonitor(root, granularity="file")
        monitor.start_session()
        monitor.begin_test("tests/test_x.py::test_a")
        ...  # test runs
        deps = monitor.end_test()
        monitor.stop_session()
    """

    def __init__(
        self,
        root: Path | str,
        granularity: str = "file",
        line_strategy: str = "local",
        excluded_dir_names: Iterable[str] = EXCLUDED_DIR_NAMES,
    ) -> None:
        if line_strategy not in ("local", "global"):
            raise ValueError(f"unknown line strategy {line_strategy!r}")
        self.root = Path(root).resolve()
        self.granularity = granularity
        self.line_strategy = line_strategy
        self._root_prefix = os.path.normcase(str(self.root)) + os.sep
        self._excluded = frozenset(excluded_dir_names)
        self._scope_cache: Dict[str, bool] = {}
        self._rel_cache: Dict[str, str] = {}
        self._current: Optional[Dict[str, Set[int]]] = None
        self._instrumented: Set[object] = set()
        self._tool_id: Optional[int] = None
        self._session_active = False
        self.stats: Dict[str, float] = {
            "py_start_events": 0,
            "line_events": 0,
            "begin_test_calls": 0,
        }

    # ------------------------------------------------------------------ setup
    @staticmethod
    def available() -> bool:
        return hasattr(sys, "monitoring") and sys.version_info >= (3, 12)

    def start_session(self) -> None:
        """Reserve a monitoring tool id and register the callbacks."""
        if self._session_active:
            return
        if not self.available():
            raise MonitoringUnavailable(
                "sys.monitoring requires CPython >= 3.12; "
                f"running {sys.version_info.major}.{sys.version_info.minor}"
            )
        mon = sys.monitoring  # type: ignore[attr-defined]
        tool_id = None
        for name in _TOOL_ID_CANDIDATES:
            candidate = getattr(mon, name)
            try:
                mon.use_tool_id(candidate, "pytest-risktest")
            except ValueError:
                continue
            tool_id = candidate
            break
        if tool_id is None:
            raise MonitoringUnavailable("no free sys.monitoring tool id is available")
        self._tool_id = tool_id
        mon.register_callback(tool_id, mon.events.PY_START, self._on_py_start)
        if self.granularity == "line":
            # The callback is registered for both strategies; whether events are
            # actually delivered is decided by the global/local event sets below.
            mon.register_callback(tool_id, mon.events.LINE, self._on_line)
        # Events stay disabled until a test actually starts, so collection,
        # reporting and idle time cost nothing.
        mon.set_events(tool_id, 0)
        self._session_active = True

    def stop_session(self) -> None:
        """Release the tool id.  Safe to call multiple times."""
        if not self._session_active or self._tool_id is None:
            return
        mon = sys.monitoring  # type: ignore[attr-defined]
        tool_id = self._tool_id
        try:
            mon.set_events(tool_id, 0)
            mon.register_callback(tool_id, mon.events.PY_START, None)
            if self.granularity == "line":
                mon.register_callback(tool_id, mon.events.LINE, None)
        except Exception:  # pragma: no cover - interpreter teardown races
            pass
        finally:
            try:
                mon.free_tool_id(tool_id)
            except Exception:  # pragma: no cover
                pass
            self._tool_id = None
            self._session_active = False
            self._current = None
            self._instrumented.clear()

    @property
    def _tracking_lines(self) -> bool:
        return self.granularity == "line"

    # -------------------------------------------------------------- per test
    def begin_test(self, nodeid: str) -> None:
        self.stats["begin_test_calls"] += 1
        self._current = {}
        self._enable()

    def end_test(self) -> Dict[str, Set[int]]:
        self._disable()
        deps = self._current or {}
        self._current = None
        return deps

    def _enable(self) -> None:
        if self._tool_id is None:
            return
        mon = sys.monitoring  # type: ignore[attr-defined]
        events = mon.events.PY_START
        if self._tracking_lines and self.line_strategy == "global":
            events |= mon.events.LINE
        if self._tracking_lines and self.line_strategy == "local":
            # Local instrumentation is reset at the end of every test, so
            # previously disabled event locations must be re-armed first.
            mon.restart_events()
        mon.set_events(self._tool_id, events)

    def _disable(self) -> None:
        if self._tool_id is None:
            return
        mon = sys.monitoring  # type: ignore[attr-defined]
        # ``set_events(tool, 0)`` clears the global set only: local events kept
        # for the per-code-object line tracing have to be turned off explicitly,
        # otherwise they would keep firing between tests.
        for code in self._instrumented:
            try:
                mon.set_local_events(self._tool_id, code, 0)
            except Exception:  # pragma: no cover - code object already collected
                pass
        self._instrumented.clear()
        mon.set_events(self._tool_id, 0)

    # ------------------------------------------------------------- callbacks
    def _on_py_start(self, code, instruction_offset) -> None:  # noqa: ANN001 - CPython signature
        self.stats["py_start_events"] += 1
        current = self._current
        if current is None:
            return
        filename = code.co_filename
        if not self._in_scope(filename):
            return
        rel = self._relative(filename)
        lines = current.get(rel)
        if lines is None:
            current[rel] = set()
        mon = sys.monitoring  # type: ignore[attr-defined]
        if self._tracking_lines and self.line_strategy == "local" and code not in self._instrumented:
            # Deferred local instrumentation: pay the function-entry event once
            # per code object, then trade it for line events in this file only.
            self._instrumented.add(code)
            try:
                mon.set_local_events(self._tool_id, code, mon.events.LINE)
            except Exception:  # pragma: no cover
                return None
            return mon.DISABLE
        return None

    def _on_line(self, code, line_number) -> None:  # noqa: ANN001 - CPython signature
        self.stats["line_events"] += 1
        current = self._current
        if current is None:
            return
        filename = code.co_filename
        if not self._in_scope(filename):
            return
        current.setdefault(self._relative(filename), set()).add(line_number)

    # ---------------------------------------------------------------- helpers
    def _in_scope(self, filename: str) -> bool:
        key = os.path.normcase(filename)
        cached = self._scope_cache.get(key)
        if cached is not None:
            return cached
        result = False
        if not filename.startswith("<"):
            absolute = os.path.normcase(os.path.abspath(filename))
            if absolute.startswith(self._root_prefix):
                parts = absolute.split(os.sep)
                result = not any(part in self._excluded for part in parts)
        self._scope_cache[key] = result
        return result

    def _relative(self, filename: str) -> str:
        rel = self._rel_cache.get(filename)
        if rel is None:
            rel = os.path.relpath(os.path.abspath(filename), str(self.root)).replace(os.sep, "/")
            self._rel_cache[filename] = rel
        return rel


def measure_overhead(root: Path | str, granularity: str, work) -> Dict[str, float]:  # noqa: ANN001
    """Run ``work`` twice (untraced / traced) and return the measured overhead.

    The helper is used by the benchmark harness and by ``tests/test_monitor.py``
    so the overhead claim in the report is reproducible rather than asserted.
    """
    import time

    started = time.perf_counter()
    work()
    baseline = time.perf_counter() - started

    monitor = DependencyMonitor(root, granularity=granularity)
    monitor.start_session()
    monitor.begin_test("<overhead>")
    started = time.perf_counter()
    work()
    traced = time.perf_counter() - started
    monitor.end_test()
    monitor.stop_session()
    overhead_pct = (traced - baseline) / baseline * 100.0 if baseline > 0 else float("nan")
    return {
        "baseline_s": baseline,
        "traced_s": traced,
        "overhead_pct": overhead_pct,
        "py_start_events": monitor.stats["py_start_events"],
        "line_events": monitor.stats["line_events"],
    }
