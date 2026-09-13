"""Tests for the command line interface (always through a real subprocess)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"


def _env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC), env.get("PYTHONPATH", "")]))
    return env


def _cli(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest_risktest", *args],
        cwd=str(cwd),
        env=_env(),
        capture_output=True,
        text=True,
        timeout=180,
    )


def _project(root: Path) -> None:
    (root / "app").mkdir(parents=True, exist_ok=True)
    (root / "app" / "__init__.py").write_text("", encoding="utf-8")
    (root / "app" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_calc.py").write_text(
        "from app.calc import add\n\n\ndef test_add():\n    assert add(1, 1) == 2\n",
        encoding="utf-8",
    )


def test_status_without_history(tmp_path):
    _project(tmp_path)
    completed = _cli(tmp_path, "status")
    assert completed.returncode == 0
    assert "tests tracked: 0" in completed.stdout


def test_version_flag(tmp_path):
    completed = _cli(tmp_path, "--version")
    assert completed.returncode == 0
    assert "pytest-risktest" in completed.stdout


def test_impact_after_a_traced_run(tmp_path):
    _project(tmp_path)
    first = _cli(
        tmp_path,
        "impact",
        "--policy",
        "off",
    )
    assert first.returncode == 0
    assert "selected:" in first.stdout
    assert "tests/test_calc.py::test_add" in first.stdout


def test_impact_forwards_pytest_options(tmp_path):
    """Regression: pytest's own options must survive the CLI's argument parsing."""
    _project(tmp_path)
    (tmp_path / "tests" / "test_other.py").write_text(
        "def test_other():\n    assert True\n", encoding="utf-8"
    )
    everything = _cli(tmp_path, "impact", "--policy", "off", "tests")
    assert everything.returncode == 0, everything.stderr
    assert "test_calc.py::test_add" in everything.stdout
    assert "test_other.py::test_other" in everything.stdout

    ignored = _cli(
        tmp_path,
        "impact",
        "--policy",
        "off",
        "tests",
        "--ignore=tests/test_other.py",
    )
    assert ignored.returncode == 0, ignored.stderr
    assert "test_calc.py::test_add" in ignored.stdout
    assert "test_other" not in ignored.stdout


def test_clean_refuses_without_confirmation(tmp_path):
    _project(tmp_path)
    completed = _cli(tmp_path, "clean")
    assert completed.returncode == 2
    assert "refusing" in completed.stdout


def test_clean_removes_state(tmp_path):
    _project(tmp_path)
    _cli(tmp_path, "status")  # creates .risktest/
    assert (tmp_path / ".risktest").exists()
    completed = _cli(tmp_path, "clean", "--yes")
    assert completed.returncode == 0
    assert not (tmp_path / ".risktest").exists()


def test_report_renders_a_stored_json_report(tmp_path):
    payload = {
        "policy": "fast",
        "granularity": "file",
        "total_tests": 4,
        "selected": 1,
        "deselected": 3,
        "skip_rate": 0.75,
        "failed": 0,
        "duration_s": 1.0,
        "reason_histogram": {"changed-dependency": 1},
        "failures": [],
    }
    report = tmp_path / "run.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    completed = _cli(tmp_path, "report", "--report", str(report))
    assert completed.returncode == 0
    assert "pytest-risktest run report" in completed.stdout
    html = _cli(tmp_path, "report", "--report", str(report), "--format", "html", "--output", str(tmp_path / "r.html"))
    assert html.returncode == 0
    assert "<svg" in (tmp_path / "r.html").read_text(encoding="utf-8")
