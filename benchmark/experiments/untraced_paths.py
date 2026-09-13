"""Boundary experiment: what dynamic tracing cannot see, and the designed escape hatch.

At *file* granularity the observed execution set proved to be a very strong
signal (no failure was missed in 36 mutation runs, see ``results/summary.md``).
It is not a complete one: a test that exercises the product across a *process
boundary* never executes the product's code in the instrumented interpreter.
Subprocess-based integration tests are the common case.

This script builds exactly that situation and measures the consequence twice:

* without a declaration the changed product file is invisible to the trace and
  the failing tests are skipped (a genuine recall failure);
* with ``@pytest.mark.risktest_always`` the tests are selected unconditionally,
  which is why the tool documents the marker as a required escape hatch for
  process-boundary tests.

Usage::

    python benchmark/experiments/untraced_paths.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
SRC = PROJECT_ROOT / "src"
RESULTS = PROJECT_ROOT / "benchmark" / "results"

sys.path.insert(0, str(SRC))

from pytest_risktest.report import markdown_table, write_json  # noqa: E402

CLI = '''"""Product entry point: normally started as a separate process."""

import sys


def total(argv):
    return sum(int(value) for value in argv)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    print(total(arguments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

TEST_PLAIN = '''import subprocess
import sys


def _run(*args):
    completed = subprocess.run(
        [sys.executable, "app/cli.py", *args], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def test_sum_via_subprocess():
    assert _run("1", "2") == "3"


def test_sum_via_subprocess_second_case():
    assert _run("2", "3") == "5"
'''

TEST_DECLARED = '''import subprocess
import sys

import pytest


def _run(*args):
    completed = subprocess.run(
        [sys.executable, "app/cli.py", *args], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


@pytest.mark.risktest_always
def test_sum_via_subprocess():
    assert _run("1", "2") == "3"


@pytest.mark.risktest_always
def test_sum_via_subprocess_second_case():
    assert _run("2", "3") == "5"
'''


def pytest_run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", *args],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


def read_report(root: Path, name: str) -> dict:
    return json.loads((root / ".risktest" / name).read_text(encoding="utf-8"))


def count_failures(output: str) -> int:
    markers = [line for line in output.splitlines() if line.strip().startswith("FAILED")]
    if markers:
        return len(markers)
    for line in output.splitlines():
        if " failed" in line and "=" in line:
            return 1
    return 0


def phase(root: Path, test_source: str, tag: str) -> dict:
    """Warm up, mutate the subprocess-only product file, then run policy=fast."""
    (root / "tests" / "test_cli.py").write_text(test_source, encoding="utf-8")
    (root / "app" / "cli.py").write_text(CLI, encoding="utf-8")
    state = root / ".risktest"
    if state.exists():
        shutil.rmtree(state)
    warm = pytest_run(
        root,
        "-p",
        "pytest_risktest.plugin",
        "--risktest",
        "--risktest-policy=off",
        f"--risktest-report=.risktest/warm-{tag}.json",
    )
    assert warm.returncode == 0, warm.stdout
    warm_report = read_report(root, f"warm-{tag}.json")

    (root / "app" / "cli.py").write_text(
        CLI.replace("sum(int(value)", "sum(int(value) * 2"), encoding="utf-8"
    )
    truth = pytest_run(root, "-rf")
    detected_truth = count_failures(truth.stdout)

    pytest_run(
        root,
        "-p",
        "pytest_risktest.plugin",
        "--risktest",
        "--risktest-policy=fast",
        f"--risktest-report=.risktest/fast-{tag}.json",
    )
    fast = read_report(root, f"fast-{tag}.json")
    return {
        "tag": tag,
        "warm_dependency_edges": warm_report["store"]["dependency_edges"],
        "ground_truth_failures": detected_truth,
        "fast_selected": fast["selected"],
        "fast_executed": fast["executed"],
        "fast_detected_failures": len(fast["failures"]),
        "fast_changed_files": fast["changed_files"],
        "fast_reasons": fast["reason_histogram"],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="risktest-untraced-") as tmp:
        root = Path(tmp) / "project"
        (root / "app").mkdir(parents=True)
        (root / "tests").mkdir(parents=True)
        (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")
        (root / "app" / "__init__.py").write_text("", encoding="utf-8")
        plain = phase(root, TEST_PLAIN, "plain")
        declared = phase(root, TEST_DECLARED, "declared")

    rows = [
        {
            "phase": "no declaration (dynamic tracing only)",
            "tests": 2,
            "selected": plain["fast_selected"],
            "executed": plain["fast_executed"],
            "real failures": plain["ground_truth_failures"],
            "detected": plain["fast_detected_failures"],
            "missed": plain["ground_truth_failures"] - plain["fast_detected_failures"],
        },
        {
            "phase": "@pytest.mark.risktest_always",
            "tests": 2,
            "selected": declared["fast_selected"],
            "executed": declared["fast_executed"],
            "real failures": declared["ground_truth_failures"],
            "detected": declared["fast_detected_failures"],
            "missed": declared["ground_truth_failures"] - declared["fast_detected_failures"],
        },
    ]
    RESULTS.mkdir(parents=True, exist_ok=True)
    markdown = (
        "# Untraced code paths (boundary experiment)\n\n"
        "The product (`app/cli.py`) only ever runs in a child process, so the\n"
        "instrumented interpreter never records it as a dependency of the tests.\n"
        "A mutation that breaks both tests is therefore invisible to a purely\n"
        "dynamic selection.\n\n"
        + markdown_table(
            rows,
            ["phase", "tests", "selected", "executed", "real failures", "detected", "missed"],
        )
        + "\n`risktest_always` is honoured independently of the policy and of the stop\n"
        "rule, which is why the documentation requires process-boundary tests to\n"
        "declare themselves.\n"
    )
    (RESULTS / "untraced-paths.md").write_text(markdown, encoding="utf-8")
    write_json(
        RESULTS / "untraced-paths.json", {"rows": rows, "raw": {"plain": plain, "declared": declared}}
    )
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

