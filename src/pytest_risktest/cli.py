"""Command line interface: ``risktest`` (also ``python -m pytest_risktest``).

The CLI is deliberately thin -- it reuses the same modules as the plugin so that
the numbers printed by the CLI and by a pytest run can never disagree.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import __version__
from .config import DEFAULT_STORE_PATH, POLICIES, policy_from_name
from .flaky import classify_pair, suspects_from_verdicts, summarize
from .graph import ImportGraph
from .report import markdown_table, read_json, render_markdown, summary_table, write_html, write_markdown
from .selector import plan_selection, resolve_change
from .store import Store

PLUGIN_ARG = "-p"
PLUGIN_PATH = "pytest_risktest.plugin"


def _root(value: str) -> Path:
    return Path(value).resolve()


def _store_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


# --------------------------------------------------------------------- helpers
class _Collector:
    """Minimal pytest plugin that records the collected node ids."""

    def __init__(self) -> None:
        self.nodeids: List[str] = []

    def pytest_collection_modifyitems(self, config, items) -> None:  # noqa: ANN001
        self.nodeids = [item.nodeid for item in items]


def collect_nodeids(root: Path, pytest_args: Sequence[str]) -> List[str]:
    import pytest

    collector = _Collector()
    pytest.main(
        ["--collect-only", "-q", "-p", "no:cacheprovider", *pytest_args],
        plugins=[collector],
    )
    return collector.nodeids


def _load_state(root: Path, store_path: str):
    store = Store(_store_path(root, store_path), root)
    previous_py = store.file_digests("py")
    previous_config = store.file_digests("config")
    previous_lines = store.line_hash_map()
    store.refresh_digests(with_lines=True)
    current_py = store.file_digests("py")
    current_config = store.file_digests("config")
    change = resolve_change(
        store=store,
        root=root,
        mode="hash",
        base_ref="HEAD",
        current_digests=current_py,
        previous_digests=previous_py,
        previous_config=previous_config,
        current_config=current_config,
    )
    changed_lines: Dict[str, set] = {}
    for path in change.changed:
        recorded = previous_lines.get(path)
        if not recorded:
            continue
        try:
            text = (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = store.changed_lines_against(recorded, text)
        if lines:
            changed_lines[path] = lines
    return store, change, changed_lines


# ------------------------------------------------------------------- commands
def cmd_status(args: argparse.Namespace) -> int:
    root = _root(args.root)
    store = Store(_store_path(root, args.store), root)
    try:
        summary = store.summary()
    finally:
        store.close()
    print(f"# risktest status -- {root}")
    print(f"- files tracked: {summary['files']}")
    print(f"- tests tracked: {summary['tests']} ({summary['tests_with_deps']} with dependencies)")
    print(f"- dependency edges: {summary['dependency_edges']}")
    print(f"- flaky suspects: {summary['flaky_tests']}")
    print(f"- outcomes recorded: {summary['outcomes']}")
    last = summary.get("last_run")
    if last:
        print(
            "- last run: {run_id} policy={policy} granularity={granularity} "
            "selected={selected}/{total} failed={failed} duration={duration:.2f}s".format(**last)
        )
    else:
        print("- last run: none recorded")
    return 0


def cmd_impact(args: argparse.Namespace) -> int:
    root = _root(args.root)
    store, change, changed_lines = _load_state(root, args.store)
    try:
        nodeids = collect_nodeids(root, args.pytest_args)
        graph = ImportGraph.from_root(root)
        plan = plan_selection(
            all_tests=nodeids,
            store=store,
            graph=graph,
            policy=policy_from_name(args.policy),
            change=change,
            granularity=args.granularity,
            changed_lines=changed_lines,
            max_deselect_pct=args.max_deselect,
            min_selected=args.min_selected,
        )
    finally:
        store.close()
    print(f"# risktest impact -- policy={plan.policy} granularity={plan.granularity}")
    print(f"- total tests: {plan.total_tests}")
    print(f"- selected: {plan.selected_count} (skip rate {plan.skip_rate:.1%})")
    print(f"- changed files: {', '.join(change.changed + change.added) or 'none'}")
    if plan.fallback:
        print(f"- fallback to a full run: {plan.fallback}")
    if plan.selected:
        rows = [
            {
                "test": nodeid,
                "reason": plan.reasons.get(nodeid, "unknown"),
                "risk": plan.risk.get(nodeid, 0.0),
            }
            for nodeid in plan.selected[: args.limit]
        ]
        print()
        print(markdown_table(rows, ["test", "reason", "risk"]))
        if plan.selected_count > args.limit:
            print(f"... {plan.selected_count - args.limit} more")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    payload = read_json(args.report)
    if args.format == "json":
        print(summary_table(payload))
        return 0
    if args.format == "html":
        target = write_html(Path(args.output), payload)
        print(f"wrote {target}")
        return 0
    markdown = render_markdown(payload)
    if args.output:
        target = write_markdown(Path(args.output), payload)
        print(f"wrote {target}")
    else:
        print(markdown, end="")
    return 0


def cmd_flaky_check(args: argparse.Namespace) -> int:
    """Run the same test set twice with different orders and diff the outcomes."""
    import pytest

    root = _root(args.root)
    store = Store(_store_path(root, args.store), root)
    reports: List[Dict[str, object]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="risktest-flaky-") as tmp:
            for index, seed in enumerate((args.seed, args.seed + 1)):
                report_path = Path(tmp) / f"run-{index}.json"
                argv = [
                    *args.pytest_args,
                    "-p",
                    PLUGIN_PATH,
                    "--risktest",
                    f"--risktest-policy={args.policy}",
                    f"--risktest-granularity={args.granularity}",
                    "--risktest-order=shuffle",
                    f"--risktest-shuffle-seed={seed}",
                    f"--risktest-store={args.store}",
                    f"--risktest-report={report_path}",
                    "-q",
                ]
                if args.verbose:
                    print(f"$ pytest {' '.join(argv)}")
                pytest.main(argv)
                reports.append(read_json(report_path))
        first = {str(k): str(v) for k, v in dict(reports[0].get("outcomes", {})).items()}  # type: ignore[arg-type]
        second = {str(k): str(v) for k, v in dict(reports[1].get("outcomes", {})).items()}  # type: ignore[arg-type]
        verdicts = classify_pair(first, second)
        suspects = list(suspects_from_verdicts(verdicts))
        if args.mark:
            store.mark_flaky(suspects, True)
        histogram = summarize(verdicts.values())
        print("# risktest flaky-check")
        print(f"- tests compared: {len(verdicts)}")
        for verdict, count in histogram.items():
            print(f"- {verdict}: {count}")
        if suspects:
            print(f"- flagged as flaky ({'stored' if args.mark else 'not stored'}):")
            for nodeid in suspects:
                print(f"  {nodeid}")
        if args.output:
            rows = [{"test": nodeid, "verdict": verdict} for nodeid, verdict in sorted(verdicts.items())]
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(markdown_table(rows, ["test", "verdict"]), encoding="utf-8")
            print(f"- wrote {target}")
    finally:
        store.close()
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    root = _root(args.root)
    target = _store_path(root, args.store)
    directory = target.parent
    if not args.yes:
        print(f"refusing to delete {directory} without --yes")
        return 2
    if directory.exists() and root in directory.resolve().parents:
        shutil.rmtree(directory)
        print(f"removed {directory}")
    else:
        print(f"nothing to remove at {directory}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="risktest",
        description="risk-aware test selection and prioritisation for pytest",
    )
    parser.add_argument("--version", action="version", version=f"pytest-risktest {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(target: argparse.ArgumentParser) -> None:
        target.add_argument("--root", default=".", help="project root (default: .)")
        target.add_argument("--store", default=DEFAULT_STORE_PATH, help="dependency store path")

    status = sub.add_parser("status", help="show what the tool knows about this repository")
    add_common(status)
    status.set_defaults(func=cmd_status)

    impact = sub.add_parser("impact", help="dry-run: show which tests a change would trigger")
    add_common(impact)
    impact.add_argument("--policy", choices=sorted(POLICIES), default="balanced")
    impact.add_argument("--granularity", choices=("file", "line"), default="file")
    impact.add_argument("--max-deselect", type=float, default=90.0)
    impact.add_argument("--min-selected", type=int, default=1)
    impact.add_argument("--limit", type=int, default=25, help="how many tests to print")
    # REMAINDER so that pytest's own options (``--ignore=...``, ``-k ...``) can be
    # forwarded without being parsed as risktest options.
    impact.add_argument(
        "pytest_args", nargs=argparse.REMAINDER, default=[], help="extra pytest arguments"
    )
    impact.set_defaults(func=cmd_impact)

    report = sub.add_parser("report", help="render the JSON report produced by a run")
    report.add_argument("--report", default=".risktest/last-run.json")
    report.add_argument("--format", choices=("markdown", "json", "html"), default="markdown")
    report.add_argument("--output", default="", help="write to a file instead of stdout")
    report.set_defaults(func=cmd_report)

    flaky = sub.add_parser("flaky-check", help="detect order-dependent tests via a perturbed rerun")
    add_common(flaky)
    flaky.add_argument("--policy", choices=sorted(POLICIES), default="off")
    flaky.add_argument("--granularity", choices=("file", "line"), default="file")
    flaky.add_argument("--seed", type=int, default=20260101)
    flaky.add_argument("--mark", action="store_true", help="store the suspects in the database")
    flaky.add_argument("--output", default="", help="write a Markdown table of verdicts")
    flaky.add_argument("--verbose", action="store_true")
    flaky.add_argument("pytest_args", nargs=argparse.REMAINDER, default=[])
    flaky.set_defaults(func=cmd_flaky_check)

    clean = sub.add_parser("clean", help="delete the local risktest state directory")
    add_common(clean)
    clean.add_argument("--yes", action="store_true")
    clean.set_defaults(func=cmd_clean)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
