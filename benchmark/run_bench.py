"""The evaluation harness: baseline -> change -> measure.

For every *target* (a repository under evaluation) the harness measures:

1. **Untraced baseline** -- plain ``pytest`` (no plugin, no tracing) with
   ``--junitxml``: the ground truth (which tests really fail) plus the wall-clock
   and execution-time cost of the naive workflow.
2. **Traced full runs** -- ``--risktest --risktest-policy=off`` with file and line
   granularity on a pristine tree: the observation cost (NFR-1).
3. **Tool runs** -- ``--risktest --risktest-policy={fast,balanced,safe}`` after a
   *verified* mutation (a mutation that provably breaks at least one test): the
   selection, its ordering, its wall clock and its safety (recall).

Two metrics are reported for the same experiment on purpose:

``time_saved``
    wall clock, including interpreter and pytest start-up (honest end-to-end
    number, dominated by fixed cost for small suites);

``work_saved``
    test execution time only, taken from the per-test durations in the JUnit XML
    and from the plugin report (isolates the effect the tool actually has).

Between mutations the dependency store is restored from a snapshot so a run can
never "see" a mutation that has already been reverted.

Run it with::

    python benchmark/run_bench.py --subjects 3 --mutations 3
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
SRC = PROJECT_ROOT / "src"
SUBJECTS_DIR = HERE / "subjects"
RESULTS_DIR = HERE / "results"
FIGURES_DIR = PROJECT_ROOT / "docs" / "report" / "figures"

sys.path.insert(0, str(SRC))

import generate_subjects  # noqa: E402  (same directory)
import mutate  # noqa: E402
from pytest_risktest.metrics import apfd, recall, skip_rate, summarize, time_saved  # noqa: E402
from pytest_risktest.report import markdown_table, svg_bar_chart, write_json  # noqa: E402

POLICIES = ("fast", "balanced", "safe")
SELF_TESTS = [
    "tests",
    "--ignore=tests/test_cli.py",
    "--ignore=tests/test_plugin_integration.py",
]
# The self-hosted target mutates only modules that the *selection path* does not
# use, so the tool being measured cannot be changed by the mutation itself.
SELF_MUTATION_FILES = [
    "src/pytest_risktest/metrics.py",
    "src/pytest_risktest/report.py",
]


@dataclass(frozen=True)
class Target:
    name: str
    root: Path
    pytest_args: Tuple[str, ...] = ()
    mutation_files: Tuple[str, ...] = ()
    store: str = ".risktest/deps.sqlite3"
    kind: str = "generated"


@dataclass
class Row:
    target: str
    kind: str
    mutation: str
    operator: str
    mutation_file: str
    mutated_line: int
    policy: str
    granularity: str
    total_tests: int
    selected: int
    executed: int
    skip_rate: float
    ground_truth_failures: int
    executed_failures: int
    misses: int
    recall: float
    apfd_baseline: float
    apfd_tool: float
    time_full_s: float
    time_tool_s: float
    time_saved: float
    work_full_s: float
    work_tool_s: float
    work_saved: float
    reasons: str = ""


@dataclass
class OverheadRow:
    target: str
    kind: str
    total_tests: int
    untraced_s: float
    traced_file_s: float
    traced_line_s: float
    overhead_file_pct: float
    overhead_line_pct: float


def _env() -> Dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC), env.get("PYTHONPATH", "")]))
    env["PYTHONHASHSEED"] = "0"
    return env


def _run(command: Sequence[str], cwd: Path, timeout: int = 900) -> Tuple[int, float, str]:
    started = time.perf_counter()
    completed = subprocess.run(
        list(command), cwd=str(cwd), env=_env(), capture_output=True, text=True, timeout=timeout
    )
    elapsed = time.perf_counter() - started
    return completed.returncode, elapsed, (completed.stdout or "") + (completed.stderr or "")


def _python() -> str:
    return sys.executable


def untraced_full_run(target: Target, junit: Path) -> Tuple[float, Dict[str, str], List[str], float]:
    """Plain pytest: ground truth, naive wall clock and execution time."""
    if junit.exists():
        junit.unlink()
    code, elapsed, output = _run(
        [
            _python(),
            "-m",
            "pytest",
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            f"--junitxml={junit}",
            *target.pytest_args,
        ],
        target.root,
    )
    outcomes: Dict[str, str] = {}
    order: List[str] = []
    work_seconds = 0.0
    if junit.exists():
        tree = ET.parse(junit)
        for case in tree.iter("testcase"):
            name = case.get("name", "")
            # ``classname`` is the dotted module path (e.g. ``tests.test_calc``);
            # pytest's ``file`` attribute is relative to the rootdir and is not
            # comparable with the plugin's node ids across invocations.
            classname = case.get("classname", "")
            module_path = (
                "/".join(classname.split(".")) + ".py" if classname else case.get("file", "")
            )
            nodeid = f"{module_path}::{name}"
            status = "passed"
            for child in case:
                if child.tag in ("failure", "error"):
                    status = "failed"
                elif child.tag == "skipped":
                    status = "skipped"
            outcomes[nodeid] = status
            order.append(nodeid)
            work_seconds += float(case.get("time") or 0.0)
    if not outcomes:  # pragma: no cover - a collection error is a benchmark failure
        raise RuntimeError(
            f"no test outcomes parsed for {target.name} (exit {code}):\n{output[-2000:]}"
        )
    return elapsed, outcomes, order, work_seconds


def _plugin_run(
    target: Target, policy: str, granularity: str, order: str, report: Path
) -> Tuple[float, dict]:
    if report.exists():
        report.unlink()
    code, elapsed, output = _run(
        [
            _python(),
            "-m",
            "pytest",
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "-p",
            "pytest_risktest.plugin",
            "--risktest",
            f"--risktest-policy={policy}",
            f"--risktest-order={order}",
            f"--risktest-granularity={granularity}",
            f"--risktest-store={target.store}",
            f"--risktest-report={report}",
            *target.pytest_args,
        ],
        target.root,
    )
    if not report.exists():  # pragma: no cover
        raise RuntimeError(f"plugin run produced no report for {target.name}:\n{output[-2000:]}")
    return elapsed, json.loads(report.read_text(encoding="utf-8"))


def checkpoint_and_snapshot(store: Path, snapshot: Path) -> None:
    """Copy the SQLite store safely (``Connection.backup`` handles WAL state)."""
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if snapshot.exists():
        snapshot.unlink()
    source = sqlite3.connect(str(store))
    try:
        destination = sqlite3.connect(str(snapshot))
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()


def restore_snapshot(snapshot: Path, store: Path) -> None:
    for suffix in ("-wal", "-shm"):
        candidate = Path(str(store) + suffix)
        if candidate.exists():
            candidate.unlink()
    shutil.copy2(snapshot, store)


def _warm_up(target: Target, work: Path) -> Tuple[OverheadRow, Path]:
    store = target.root / target.store
    state_dir = store.parent
    if state_dir.exists():
        shutil.rmtree(state_dir)
    untraced_seconds, pristine, _, _ = untraced_full_run(target, work / "baseline.xml")
    failing = [nodeid for nodeid, status in pristine.items() if status == "failed"]
    if failing:  # pragma: no cover - targets must start green
        raise RuntimeError(f"target {target.name} is not green: {failing[:5]}")
    traced_file_seconds, _ = _plugin_run(target, "off", "file", "original", work / "warm-file.json")
    traced_line_seconds, _ = _plugin_run(target, "off", "line", "original", work / "warm-line.json")
    overhead = OverheadRow(
        target=target.name,
        kind=target.kind,
        total_tests=len(pristine),
        untraced_s=round(untraced_seconds, 4),
        traced_file_s=round(traced_file_seconds, 4),
        traced_line_s=round(traced_line_seconds, 4),
        overhead_file_pct=round((traced_file_seconds / untraced_seconds - 1) * 100, 2),
        overhead_line_pct=round((traced_line_seconds / untraced_seconds - 1) * 100, 2),
    )
    snapshot = work / "store-snapshot.sqlite3"
    checkpoint_and_snapshot(store, snapshot)
    return overhead, snapshot


def _apply_killing_mutation(
    target: Target, seed: int, work: Path, attempt_tag: str, max_attempts: int = 12
) -> Tuple[Optional[mutate.Mutation], Optional[Tuple[float, Dict[str, str], List[str], float]]]:
    """Apply a mutation and keep it only if it breaks at least one test."""
    for attempt in range(max_attempts):
        applied = mutate.apply_mutation(
            target.root,
            seed=seed + attempt * 104729,
            files=list(target.mutation_files) or None,
            prefer="flip-boolean-return" if attempt % 3 == 0 else None,
        )
        if applied is None:
            return None, None
        measurement = untraced_full_run(target, work / f"gt-{attempt_tag}.xml")
        failing = [nodeid for nodeid, status in measurement[1].items() if status == "failed"]
        if failing:
            return applied, measurement
        mutate.revert(target.root, applied)
    return None, None


def benchmark_target(
    target: Target, mutations_per_target: int, granularity: str, work_root: Path, seed: int
) -> Tuple[List[Row], OverheadRow, List[str]]:
    work = work_root / target.name
    work.mkdir(parents=True, exist_ok=True)
    overhead, snapshot = _warm_up(target, work)
    store = target.root / target.store
    rows: List[Row] = []
    notes: List[str] = []

    for index in range(mutations_per_target):
        seed_for_mutation = seed + 7919 * (index + 1) + sum(ord(char) for char in target.name)
        applied, measurement = _apply_killing_mutation(
            target, seed_for_mutation, work, attempt_tag=f"{index}"
        )
        if applied is None or measurement is None:
            notes.append(f"{target.name}: no killing mutation found for slot {index}")
            continue
        time_full, failures, full_order, work_full = measurement
        failing = [nodeid for nodeid, status in failures.items() if status == "failed"]
        try:
            for policy in POLICIES:
                # Every policy must observe the same pristine -> mutated
                # transition: the plugin refreshes the file digests when it
                # collects, so without this restore the second policy run would
                # see an unchanged tree and select only the always-run set.
                restore_snapshot(snapshot, store)
                report_path = work / f"tool-{index}-{policy}.json"
                time_tool, report = _plugin_run(target, policy, granularity, "risk", report_path)
                executed = [
                    nodeid
                    for nodeid, status in report["outcomes"].items()
                    if status != "skipped"
                ]
                hit = sum(1 for nodeid in executed if nodeid in set(failing))
                work_tool = sum(report["durations"].values())
                rows.append(
                    Row(
                        target=target.name,
                        kind=target.kind,
                        mutation=f"{target.name}-m{index}",
                        operator=applied.operator,
                        mutation_file=applied.path,
                        mutated_line=applied.line,
                        policy=policy,
                        granularity=granularity,
                        total_tests=len(failures),
                        selected=report["selected"],
                        executed=len(executed),
                        skip_rate=round(skip_rate(executed, list(failures)), 4),
                        ground_truth_failures=len(failing),
                        executed_failures=hit,
                        misses=len(failing) - hit,
                        recall=round(recall(executed, failing), 4),
                        apfd_baseline=round(apfd(full_order, failing, list(failures)), 4),
                        apfd_tool=round(apfd(list(report["selected_tests"]), failing, list(failures)), 4),
                        time_full_s=round(time_full, 4),
                        time_tool_s=round(time_tool, 4),
                        time_saved=round(time_saved(time_full, time_tool), 4),
                        work_full_s=round(work_full, 4),
                        work_tool_s=round(work_tool, 4),
                        work_saved=round(time_saved(work_full, work_tool), 4),
                        reasons=json.dumps(report["reason_histogram"], sort_keys=True),
                    )
                )
        finally:
            mutate.revert(target.root, applied)
            restore_snapshot(snapshot, store)
    return rows, overhead, notes


def write_outputs(rows: List[Row], overhead: List[OverheadRow], notes: List[str]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULTS_DIR / "benchmark.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(Row.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    def aggregate(rows_subset: List[Row], key: str) -> float:
        return round(summarize([getattr(row, key) for row in rows_subset])["mean"], 4)

    by_policy: Dict[str, List[Row]] = {}
    for row in rows:
        by_policy.setdefault(row.policy, []).append(row)
    by_kind_and_policy: Dict[Tuple[str, str], List[Row]] = {}
    for row in rows:
        by_kind_and_policy.setdefault((row.kind, row.policy), []).append(row)

    policy_rows = [
        {
            "policy": policy,
            "runs": len(group),
            "skip_rate": aggregate(group, "skip_rate"),
            "recall": round(min(row.recall for row in group), 4),
            "misses": sum(row.misses for row in group),
            "apfd_tool": aggregate(group, "apfd_tool"),
            "apfd_baseline": aggregate(group, "apfd_baseline"),
            "time_saved": aggregate(group, "time_saved"),
            "work_saved": aggregate(group, "work_saved"),
        }
        for policy, group in sorted(by_policy.items())
    ]
    kind_rows = [
        {
            "target kind": kind,
            "policy": policy,
            "runs": len(group),
            "skip_rate": aggregate(group, "skip_rate"),
            "recall": round(min(row.recall for row in group), 4),
            "misses": sum(row.misses for row in group),
            "apfd_tool": aggregate(group, "apfd_tool"),
            "work_saved": aggregate(group, "work_saved"),
        }
        for (kind, policy), group in sorted(by_kind_and_policy.items())
    ]
    overhead_rows = [asdict(row) for row in overhead]

    write_json(
        RESULTS_DIR / "benchmark.json",
        {
            "rows": [asdict(row) for row in rows],
            "per_policy": policy_rows,
            "per_target_kind": kind_rows,
            "overhead": overhead_rows,
            "notes": notes,
            "generated_by": "benchmark/run_bench.py",
        },
    )

    lines = [
        "# Benchmark summary",
        "",
        f"- mutation runs: {len(rows)}",
        f"- targets: {', '.join(sorted({row.target for row in rows}))}",
        f"- policies: {', '.join(sorted(by_policy))}",
        "",
        "## Selection quality per policy",
        "",
        markdown_table(
            policy_rows,
            ["policy", "runs", "skip_rate", "recall", "misses", "apfd_tool",
             "apfd_baseline", "time_saved", "work_saved"],
        ),
        "`recall` is reported as the worst case over all runs: it is the safety metric,",
        "so the minimum matters rather than the mean.",
        "",
        "## Generated vs self-hosted targets",
        "",
        markdown_table(
            kind_rows,
            ["target kind", "policy", "runs", "skip_rate", "recall", "misses", "apfd_tool", "work_saved"],
        ),
        "## Observation overhead",
        "",
        markdown_table(
            overhead_rows,
            ["target", "kind", "total_tests", "untraced_s", "traced_file_s",
             "traced_line_s", "overhead_file_pct", "overhead_line_pct"],
        ),
        "## Per-mutation detail",
        "",
        markdown_table(
            [
                {
                    "mutation": row.mutation,
                    "operator": row.operator,
                    "file": f"{row.mutation_file}:{row.mutated_line}",
                    "policy": row.policy,
                    "selected": row.selected,
                    "total": row.total_tests,
                    "skip_rate": row.skip_rate,
                    "failures": row.ground_truth_failures,
                    "recall": row.recall,
                    "misses": row.misses,
                    "apfd_tool": row.apfd_tool,
                    "work_saved": row.work_saved,
                }
                for row in rows
            ]
        ),
    ]
    if notes:
        lines += ["## Notes", ""] + [f"- {note}" for note in notes]
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for metric in ("skip_rate", "recall", "apfd_tool", "time_saved", "work_saved"):
        data = {row["policy"]: float(row[metric]) for row in policy_rows}
        (FIGURES_DIR / f"benchmark-{metric.replace('_', '-')}.svg").write_text(
            svg_bar_chart(data, title=f"{metric} by policy"), encoding="utf-8"
        )
    if overhead_rows:
        (FIGURES_DIR / "benchmark-overhead.svg").write_text(
            svg_bar_chart(
                {row["target"]: float(row["overhead_file_pct"]) for row in overhead_rows},
                title="Tracing overhead (file granularity, %)",
            ),
            encoding="utf-8",
        )


def build_targets(subject_count: int, seed: int, features: int, iterations: int) -> List[Target]:
    subjects = generate_subjects.generate(
        subject_count, seed, SUBJECTS_DIR, clean=True, features=features, iterations=iterations
    )
    targets = [Target(name=subject.name, root=subject, kind="generated") for subject in subjects]
    targets.append(
        Target(
            name="pytest-risktest (self-hosted)",
            root=PROJECT_ROOT,
            pytest_args=tuple(SELF_TESTS),
            mutation_files=tuple(SELF_MUTATION_FILES),
            store=".risktest/bench-self.sqlite3",
            kind="self-hosted",
        )
    )
    return targets


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subjects", type=int, default=3, help="generated subjects (plus the self target)")
    parser.add_argument("--mutations", type=int, default=3, help="verified mutations per target")
    parser.add_argument("--seed", type=int, default=20260101)
    parser.add_argument("--features", type=int, default=8)
    parser.add_argument("--iterations", type=int, default=45000)
    parser.add_argument("--granularity", choices=("file", "line"), default="file")
    parser.add_argument("--keep-work", action="store_true")
    parser.add_argument("--targets", default="", help="comma separated target names to run")
    args = parser.parse_args(argv)

    targets = build_targets(args.subjects, args.seed, args.features, args.iterations)
    if args.targets:
        wanted = {name.strip() for name in args.targets.split(",") if name.strip()}
        targets = [target for target in targets if target.name in wanted]
    work_root = SUBJECTS_DIR / "_work"
    if work_root.exists():
        shutil.rmtree(work_root)

    all_rows: List[Row] = []
    overhead: List[OverheadRow] = []
    notes: List[str] = []
    for target in targets:
        print(f"[bench] {target.name} ({target.kind}) ...", flush=True)
        rows, row_overhead, target_notes = benchmark_target(
            target, args.mutations, args.granularity, work_root, seed=args.seed
        )
        all_rows.extend(rows)
        overhead.append(row_overhead)
        notes.extend(target_notes)
        print(
            f"[bench] {target.name}: {len(rows)} runs, {row_overhead.total_tests} tests, "
            f"overhead file={row_overhead.overhead_file_pct}% line={row_overhead.overhead_line_pct}%",
            flush=True,
        )

    write_outputs(all_rows, overhead, notes)
    if not args.keep_work:
        shutil.rmtree(work_root, ignore_errors=True)
    print(f"[bench] wrote {RESULTS_DIR / 'benchmark.csv'} and {RESULTS_DIR / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
