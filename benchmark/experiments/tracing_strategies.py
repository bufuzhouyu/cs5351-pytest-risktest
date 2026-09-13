"""Design-option experiment for NFR-1: how should line-level tracing be enabled?

The evaluation found that enabling ``LINE`` globally through
``sys.monitoring.set_events`` inflates the runtime of a CPU-bound suite by more
than 6x, while ``PY_START`` (file granularity) costs almost nothing.  This script
measures the three candidate strategies on one controlled workload so the
architectural decision documented in ``docs/04-architecture.md`` is backed by
numbers:

* ``none``        -- no observation at all (lower bound);
* ``file``        -- ``PY_START`` only;
* ``line-global`` -- ``LINE`` enabled for the whole interpreter;
* ``line-local``  -- ``LINE`` enabled lazily per project code object (the chosen
  design: function-entry events are traded for line events once, and code objects
  outside the project never pay for line events).

Two workloads are used, because the answer depends on *where* the hot code lives:

``hot-loop``
    a tight loop inside a project file -- the worst case for any line tracer;

``library-bound``
    a tight loop whose body is dominated by standard-library Python code
    (``json.dumps``) -- the case where per-code-object instrumentation wins,
    because the library code objects are never instrumented at all.

Usage::

    python benchmark/experiments/tracing_strategies.py --iterations 200000
"""

from __future__ import annotations

import argparse
import json
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
SRC = PROJECT_ROOT / "src"
RESULTS = PROJECT_ROOT / "benchmark" / "results"
FIGURES = PROJECT_ROOT / "docs" / "report" / "figures"

sys.path.insert(0, str(SRC))

from pytest_risktest.monitor import DependencyMonitor  # noqa: E402
from pytest_risktest.report import markdown_table, svg_bar_chart  # noqa: E402
from pytest_risktest.store import hash_lines  # noqa: E402  (import cost paid once, outside timing)


def workload(iterations: int) -> int:
    """A tight loop inside one function: the worst case for line tracing."""
    total = 0
    for index in range(iterations):
        total += index % 7
    return total


PAYLOAD = {"items": [{"id": index, "tags": ["a", "b", "c"]} for index in range(40)]}


def library_workload(iterations: int) -> int:
    """A loop dominated by standard-library Python code."""
    size = 0
    for _ in range(iterations):
        size += len(json.dumps(PAYLOAD))
    return size


def measure(strategy: str, workload_fn, iterations: int, repeats: int = 5) -> float:
    monitor = None
    if strategy != "none":
        granularity = "file" if strategy == "file" else "line"
        line_strategy = "local" if strategy == "line-local" else "global"
        monitor = DependencyMonitor(PROJECT_ROOT, granularity=granularity, line_strategy=line_strategy)
    best = float("inf")
    for _ in range(repeats):
        if monitor is not None:
            monitor.start_session()
            monitor.begin_test("bench")
        started = time.perf_counter()
        workload_fn(iterations)
        elapsed = time.perf_counter() - started
        if monitor is not None:
            monitor.end_test()
            monitor.stop_session()
        best = min(best, elapsed)
    return best


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=200000)
    parser.add_argument("--library-iterations", type=int, default=400)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args(argv)

    strategies = ["none", "file", "line-local", "line-global"]
    workloads = {
        "hot-loop": (workload, args.iterations, max(3, args.repeats)),
        "library-bound": (library_workload, args.library_iterations, max(3, args.repeats)),
    }
    rows = []
    for name, (fn, iterations, repeats) in workloads.items():
        timings = {
            strategy: measure(strategy, fn, iterations, repeats) for strategy in strategies
        }
        baseline = timings["none"]
        for strategy in strategies:
            rows.append(
                {
                    "workload": name,
                    "strategy": strategy,
                    "iterations": iterations,
                    "seconds": round(timings[strategy], 4),
                    "overhead_pct": round((timings[strategy] / baseline - 1) * 100, 2),
                }
            )
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    (RESULTS / "tracing-strategies.json").write_text(
        json.dumps(
            {
                "iterations": args.iterations,
                "repeats": args.repeats,
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (RESULTS / "tracing-strategies.md").write_text(
        "# Line-tracing strategies (NFR-1 design option)\n\n"
        f"Best of {args.repeats} runs per configuration.\n\n"
        + markdown_table(rows, ["workload", "strategy", "iterations", "seconds", "overhead_pct"]),
        encoding="utf-8",
    )
    (FIGURES / "tracing-strategies.svg").write_text(
        svg_bar_chart(
            {f"{row['workload']}/{row['strategy']}": float(row["overhead_pct"]) for row in rows},
            title="Tracing overhead by workload and strategy (%)",
        ),
        encoding="utf-8",
    )
    print(markdown_table(rows, ["workload", "strategy", "iterations", "seconds", "overhead_pct"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
