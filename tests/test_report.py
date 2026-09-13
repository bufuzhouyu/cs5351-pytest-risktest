"""Tests for report rendering."""

from __future__ import annotations

from pytest_risktest.report import (
    markdown_table,
    read_json,
    render_html,
    render_markdown,
    svg_bar_chart,
    summary_table,
    write_html,
    write_json,
    write_markdown,
)

PAYLOAD = {
    "policy": "balanced",
    "granularity": "file",
    "total_tests": 10,
    "selected": 3,
    "deselected": 7,
    "skip_rate": 0.7,
    "failed": 1,
    "duration_s": 1.25,
    "reason_histogram": {"changed-dependency": 2, "flaky-suspect": 1},
    "changed_files": ["app/calc.py"],
    "failures": ["tests/test_calc.py::test_add"],
    "flaky_findings": {"tests/test_text.py::test_shout": "nondeterministic"},
}


def test_json_roundtrip(tmp_path):
    target = write_json(tmp_path / "out" / "report.json", PAYLOAD)
    assert target.exists()
    assert read_json(target)["policy"] == "balanced"


def test_markdown_contains_key_numbers():
    markdown = render_markdown(PAYLOAD)
    assert "pytest-risktest run report" in markdown
    assert "changed-dependency" in markdown
    assert "tests/test_calc.py::test_add" in markdown
    assert "nondeterministic" in markdown


def test_markdown_handles_empty_failures():
    payload = {**PAYLOAD, "failures": [], "flaky_findings": {}}
    assert "- none" in render_markdown(payload)


def test_html_is_self_contained():
    document = render_html(PAYLOAD)
    assert document.startswith("<!doctype html>")
    assert "<svg" in document
    assert "changed-dependency" in document


def test_svg_bar_chart_is_well_formed():
    svg = svg_bar_chart({"a": 1, "b": 2}, title="demo")
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "demo" in svg
    assert 'rect x="' in svg


def test_svg_bar_chart_without_data():
    assert "<svg" in svg_bar_chart({})


def test_summary_table_lists_metrics():
    table = summary_table(PAYLOAD)
    assert "| policy | balanced |" in table


def test_markdown_table_renders_rows():
    table = markdown_table([{"a": 1, "b": 2.5}], ["a", "b"])
    assert table.splitlines()[0] == "| a | b |"
    assert "| 1 | 2.500 |" in table
    assert markdown_table([]) == ""


def test_write_helpers_create_files(tmp_path):
    assert write_markdown(tmp_path / "r.md", PAYLOAD).exists()
    assert write_html(tmp_path / "r.html", PAYLOAD).exists()

