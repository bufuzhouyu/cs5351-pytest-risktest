"""Tests for the static import graph."""

from __future__ import annotations

from conftest import make_project
from pytest_risktest.graph import ImportGraph, is_test_file, module_index, static_imports


def test_module_index_maps_dotted_names(tmp_path):
    make_project(tmp_path)
    index = module_index(tmp_path)
    assert index["app"] == "app/__init__.py"
    assert index["app.calc"] == "app/calc.py"
    assert index["tests.test_calc"] == "tests/test_calc.py"


def test_static_imports_finds_test_dependencies(tmp_path):
    make_project(tmp_path)
    imports = static_imports(tmp_path)
    assert "app/calc.py" in imports["tests/test_calc.py"]
    assert "app/text.py" in imports["tests/test_text.py"]


def test_relative_imports_are_resolved(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("from .core import run\n", encoding="utf-8")
    (tmp_path / "pkg" / "core.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    imports = static_imports(tmp_path)
    assert imports["pkg/__init__.py"] == {"pkg/core.py"}


def test_import_graph_reverse_dependencies(tmp_path):
    make_project(tmp_path)
    graph = ImportGraph.from_root(tmp_path)
    importers = graph.importers_of("app/calc.py")
    assert "tests/test_calc.py" in importers
    assert "app/__init__.py" in importers


def test_affected_by_depth_zero_is_empty(tmp_path):
    make_project(tmp_path)
    graph = ImportGraph.from_root(tmp_path)
    assert graph.affected_by(["app/calc.py"], 0) == set()


def test_affected_by_depth_one(tmp_path):
    make_project(tmp_path)
    graph = ImportGraph.from_root(tmp_path)
    affected = graph.affected_by(["app/calc.py"], 1)
    assert "tests/test_calc.py" in affected
    assert "app/__init__.py" in affected


def test_affected_by_closure_is_transitive(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "low.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pkg" / "mid.py").write_text("from pkg.low import VALUE\n", encoding="utf-8")
    (tmp_path / "pkg" / "high.py").write_text("from pkg.mid import VALUE\n", encoding="utf-8")
    graph = ImportGraph.from_root(tmp_path)
    affected = graph.affected_by(["pkg/low.py"], None)
    assert {"pkg/mid.py", "pkg/high.py"} <= affected
    assert graph.affected_by(["pkg/low.py"], 1) == {"pkg/mid.py"}


def test_affected_by_never_returns_the_changed_file_itself(tmp_path):
    make_project(tmp_path)
    graph = ImportGraph.from_root(tmp_path)
    assert "app/calc.py" not in graph.affected_by(["app/calc.py"], None)


def test_is_test_file_recognises_conventions():
    assert is_test_file("tests/test_calc.py")
    assert is_test_file("tests/helpers.py")
    assert is_test_file("app/test_something.py")
    assert is_test_file("app/calc_test.py")
    assert not is_test_file("app/calc.py")


def test_syntax_error_file_does_not_break_scan(tmp_path):
    make_project(tmp_path)
    (tmp_path / "app" / "broken.py").write_text("def oops(:\n", encoding="utf-8")
    imports = static_imports(tmp_path)
    assert imports["app/broken.py"] == set()

