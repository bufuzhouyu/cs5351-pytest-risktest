"""End-to-end tests: the plugin is exercised through real pytest subprocesses.

These tests are the project's acceptance tests for the user stories in
``docs/03-requirements.md``:

* a warm-up run records traces and executes everything;
* an unchanged file triggers no skips;
* a changed file triggers exactly the tests that exercised it;
* a change that breaks a test is never hidden by the selection;
* configuration changes force a full run;
* the stop rule caps the skip rate;
* ``@pytest.mark.risktest_always`` overrides the selection.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

CALC = """def add(a, b):
    return a + b


def is_even(value):
    return value % 2 == 0
"""

TEXT = """def shout(text):
    return text.upper()
"""

TEST_CALC = """from app.calc import add, is_even


def test_add():
    assert add(1, 2) == 3


def test_is_even():
    assert is_even(4)
"""

TEST_TEXT = """from app.text import shout


def test_shout():
    assert shout("hi") == "HI"
"""


@pytest.fixture(autouse=True)
def _plugin_importable(monkeypatch: pytest.MonkeyPatch) -> None:
    existing = os.environ.get("PYTHONPATH", "")
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(filter(None, [str(SRC), existing])))


def _make_project(pytester: pytest.Pytester) -> Path:
    root = pytester.path
    (root / "app").mkdir(parents=True, exist_ok=True)
    (root / "app" / "__init__.py").write_text("", encoding="utf-8")
    (root / "app" / "calc.py").write_text(CALC, encoding="utf-8")
    (root / "app" / "text.py").write_text(TEXT, encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_calc.py").write_text(TEST_CALC, encoding="utf-8")
    (root / "tests" / "test_text.py").write_text(TEST_TEXT, encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")
    return root


def _write_source(root: Path, relative: str, text: str) -> None:
    """Write a source file and drop cached bytecode.

    CPython invalidates a cached ``.pyc`` using the source *size* and the mtime
    rounded to **seconds**.  A test that applies a same-length edit within the same
    second as the previous run would otherwise execute the previous bytecode and
    observe no change at all.
    """
    import shutil

    (root / relative).write_text(text, encoding="utf-8")
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _run(pytester: pytest.Pytester, *args: str):
    return pytester.runpytest_subprocess("-p", "pytest_risktest.plugin", *args)


def _report(root: Path, name: str = ".risktest/last-run.json"):
    return json.loads((root / name).read_text(encoding="utf-8"))


def test_warmup_run_traces_everything(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    result = _run(pytester, "--risktest", "--risktest-policy=off")
    result.assert_outcomes(passed=3)
    report = _report(root)
    assert report["trace_only"] is True
    assert report["selected"] == 3
    assert report["deselected"] == 0
    assert report["reason_histogram"] == {"policy-off": 3}
    assert (root / ".risktest" / "deps.sqlite3").exists()
    assert report["store"]["tests_with_deps"] == 3


def test_unchanged_tree_runs_only_the_minimum(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    _run(pytester, "--risktest", "--risktest-policy=off")
    result = _run(pytester, "--risktest", "--risktest-policy=fast", "--risktest-report=.risktest/second.json")
    result.assert_outcomes(passed=1, deselected=2)
    report = _report(root, ".risktest/second.json")
    assert report["changed_files"] == []
    assert report["selected"] == 1


def test_changed_module_selects_only_its_tests(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    _run(pytester, "--risktest", "--risktest-policy=off")
    _write_source(
        root, "app/calc.py", CALC.replace("    return a + b\n", "    return a + b  # touched\n")
    )
    result = _run(pytester, "--risktest", "--risktest-policy=fast")
    result.assert_outcomes(passed=2, deselected=1)
    report = _report(root)
    assert report["changed_files"] == ["app/calc.py"]
    assert all("test_calc" in nodeid for nodeid in report["selected_tests"])


def test_failure_caused_by_the_change_is_never_hidden(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    _run(pytester, "--risktest", "--risktest-policy=off")
    _write_source(root, "app/calc.py", CALC.replace("return a + b", "return a - b"))
    result = _run(pytester, "--risktest", "--risktest-policy=fast")
    result.assert_outcomes(failed=1, passed=1, deselected=1)
    report = _report(root)
    assert report["failures"] == ["tests/test_calc.py::test_add"]


def test_configuration_change_forces_a_full_run(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    _run(pytester, "--risktest", "--risktest-policy=off")
    (root / "pyproject.toml").write_text("[project]\nname = 'demo2'\n", encoding="utf-8")
    result = _run(pytester, "--risktest", "--risktest-policy=fast")
    result.assert_outcomes(passed=3)
    report = _report(root)
    assert report["fallback"] == "configuration files changed"
    assert report["config_changed"] == ["pyproject.toml"]


def test_stop_rule_caps_the_skip_rate(pytester: pytest.Pytester) -> None:
    _make_project(pytester)
    _run(pytester, "--risktest", "--risktest-policy=off")
    result = _run(pytester, "--risktest", "--risktest-policy=fast", "--risktest-max-deselect=0")
    result.assert_outcomes(passed=3)


def test_always_run_marker_overrides_selection(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    (root / "tests" / "test_smoke.py").write_text(
        "import pytest\n\n\n"
        "@pytest.mark.risktest_always\n"
        "def test_smoke():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    _run(pytester, "--risktest", "--risktest-policy=off")
    _write_source(root, "app/unrelated.py", "VALUE = 1\n")
    result = _run(pytester, "--risktest", "--risktest-policy=fast")
    result.assert_outcomes(passed=1, deselected=3)
    report = _report(root)
    assert report["selected_tests"] == ["tests/test_smoke.py::test_smoke"]
    assert report["reason_histogram"] == {"always-run": 1}


def test_line_granularity_records_changed_lines(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    _run(pytester, "--risktest", "--risktest-policy=off", "--risktest-granularity=line")
    _write_source(root, "app/calc.py", CALC.replace("    return a + b\n", "    return b + a\n"))
    result = _run(
        pytester, "--risktest", "--risktest-policy=fast", "--risktest-granularity=line"
    )
    result.assert_outcomes(passed=2, deselected=1)
    report = _report(root)
    assert "changed-line" in report["reason_histogram"] or "changed-dependency" in report["reason_histogram"]


def test_plugin_is_inert_without_the_flag(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    result = _run(pytester)
    result.assert_outcomes(passed=3)
    assert not (root / ".risktest").exists()


def test_reports_are_written_in_three_formats(pytester: pytest.Pytester) -> None:
    root = _make_project(pytester)
    _run(pytester, "--risktest", "--risktest-policy=off", "--risktest-report=out/run.json")
    assert (root / "out" / "run.json").exists()
    assert (root / "out" / "run.md").exists()
    assert (root / "out" / "run.html").exists()
