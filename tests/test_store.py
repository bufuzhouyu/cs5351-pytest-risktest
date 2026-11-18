"""Tests for the SQLite persistence layer."""

from __future__ import annotations

from conftest import make_project
from pytest_risktest.store import (
    Store,
    changed_line_numbers,
    dependency_fingerprint,
    digest_bytes,
    hash_lines,
)


def _store(tmp_path):
    return Store(tmp_path / ".risktest" / "deps.sqlite3", tmp_path)


def test_store_creates_missing_directories(tmp_path):
    store = Store(tmp_path / "deep" / "nested" / "store.sqlite3", tmp_path)
    assert store.path.exists()
    store.close()


def test_refresh_digests_tracks_python_and_config_files(tmp_path):
    make_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    with _store(tmp_path) as store:
        store.refresh_digests()
        assert "app/calc.py" in store.file_digests("py")
        assert "pyproject.toml" in store.file_digests("config")


def test_change_detection_reports_modified_added_removed(tmp_path):
    make_project(tmp_path)
    with _store(tmp_path) as store:
        store.refresh_digests()
        previous = store.file_digests("py")
        previous_config = store.file_digests("config")

        (tmp_path / "app" / "calc.py").write_text(
            "def add(a, b):\n    return a + b\n\n\ndef is_even(value):\n    return value % 2 == 1\n",
            encoding="utf-8",
        )
        (tmp_path / "app" / "new.py").write_text("VALUE = 1\n", encoding="utf-8")
        (tmp_path / "app" / "text.py").unlink()
        store.refresh_digests()

        from pytest_risktest.selector import resolve_change

        change = resolve_change(
            store=store,
            root=tmp_path,
            mode="hash",
            base_ref="HEAD",
            current_digests=store.file_digests("py"),
            previous_digests=previous,
            previous_config=previous_config,
            current_config=store.file_digests("config"),
        )
    assert change.changed == ["app/calc.py"]
    assert change.added == ["app/new.py"]
    assert change.removed == ["app/text.py"]
    assert change.requires_full_run is False


def test_config_change_requires_full_run(tmp_path):
    make_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    with _store(tmp_path) as store:
        store.refresh_digests()
        previous_py = store.file_digests("py")
        previous_config = store.file_digests("config")
        (tmp_path / "pyproject.toml").write_text("[project]\nname='y'\n", encoding="utf-8")
        store.refresh_digests()
        from pytest_risktest.selector import resolve_change

        change = resolve_change(
            store=store,
            root=tmp_path,
            mode="hash",
            base_ref="HEAD",
            current_digests=store.file_digests("py"),
            previous_digests=previous_py,
            previous_config=previous_config,
            current_config=store.file_digests("config"),
        )
    assert change.config_changed == ["pyproject.toml"]
    assert change.requires_full_run is True


def test_dependency_roundtrip_and_reverse_index(tmp_path):
    make_project(tmp_path)
    with _store(tmp_path) as store:
        store.record_test_dependencies(
            "tests/test_calc.py::test_add", {"app/calc.py": {1, 2, 3}}, "fp1"
        )
        store.record_test_dependencies(
            "tests/test_text.py::test_shout", {"app/text.py": set()}, "fp2"
        )
        assert store.dependencies_of("tests/test_calc.py::test_add") == {"app/calc.py": {1, 2, 3}}
        index = store.tests_touching(["app/calc.py", "app/text.py"])
        assert index["app/calc.py"] == {"tests/test_calc.py::test_add"}
        assert index["app/text.py"] == {"tests/test_text.py::test_shout"}
        assert store.line_hits("tests/test_calc.py::test_add", "app/calc.py") == {1, 2, 3}


def test_recording_dependencies_replaces_previous_edges(tmp_path):
    with _store(tmp_path) as store:
        store.record_test_dependencies("t", {"a.py": {1}}, "fp")
        store.record_test_dependencies("t", {"b.py": {2}}, "fp2")
        assert store.dependencies_of("t") == {"b.py": {2}}
        assert store.tests_touching(["a.py"]) == {}


def test_outcomes_update_state_and_flags(tmp_path):
    with _store(tmp_path) as store:
        store.record_outcomes("run1", {"t": "failed"}, {"t": 0.5}, {"t": "fp"})
        store.record_outcomes("run2", {"t": "passed"}, {"t": 0.4}, {"t": "fp"})
        states = store.test_states()
        assert states["t"].n_runs == 2
        assert states["t"].n_failures == 1
        assert states["t"].last_status == "passed"
        assert states["t"].failed_last_run is False
        assert states["t"].failure_rate == 0.5
        assert store.recent_statuses("t") == ["passed", "failed"]


def test_outcome_history_is_pruned(tmp_path):
    with _store(tmp_path) as store:
        for index in range(30):
            store.record_outcomes(f"run{index}", {"t": "passed"}, {"t": 0.1}, {"t": "fp"})
        assert len(store.recent_statuses("t", limit=100)) == 20


def test_mark_flaky_and_always_run(tmp_path):
    with _store(tmp_path) as store:
        store.record_outcomes("run1", {"t": "passed"}, {"t": 0.1}, {"t": "fp"})
        store.mark_flaky(["t"], True)
        store.set_always_run("t", True)
        state = store.test_states()["t"]
        assert state.flaky is True
        assert state.always_run is True
        store.mark_flaky(["t"], False)
        assert store.test_states()["t"].flaky is False


def test_prune_tests_removes_stale_entries(tmp_path):
    with _store(tmp_path) as store:
        store.record_test_dependencies("old", {"a.py": set()}, "fp")
        store.record_outcomes("run1", {"old": "passed"}, {"old": 1.0}, {"old": "fp"})
        removed = store.prune_tests(["new"])
        assert removed == 1
        assert store.known_tests() == set()
        assert store.tests_touching(["a.py"]) == {}


def test_run_summary_and_status_summary(tmp_path):
    with _store(tmp_path) as store:
        store.record_test_dependencies("t", {"a.py": set()}, "fp")
        store.record_run_summary("run1", "balanced", "file", 1, 4, 0, 1.5)
        summary = store.summary()
        assert summary["tests"] == 1
        assert summary["dependency_edges"] == 1
        assert summary["last_run"]["policy"] == "balanced"
        assert summary["last_run"]["total"] == 4


def test_dependency_fingerprint_is_stable_and_sensitive(tmp_path):
    digests = {"a.py": "aaa", "b.py": "bbb"}
    first = dependency_fingerprint({"a.py": {1, 2}}, digests)
    assert first == dependency_fingerprint({"a.py": {2, 1}}, digests)
    assert first != dependency_fingerprint({"a.py": {1, 3}}, digests)
    assert first != dependency_fingerprint({"a.py": {1, 2}}, {"a.py": "different"})
    assert first != dependency_fingerprint({"a.py": {1, 2}, "b.py": set()}, digests)


def test_digest_and_line_hashes(tmp_path):
    assert digest_bytes(b"abc") == digest_bytes(b"abc")
    assert digest_bytes(b"abc") != digest_bytes(b"abd")
    assert len(hash_lines("a\nb\n")) == 2


def test_changed_line_numbers_detects_replacements_and_insertions():
    old = hash_lines("a\nb\nc\n")
    new = hash_lines("a\nB\nc\n")
    assert changed_line_numbers(old, new) == {2}
    inserted = hash_lines("a\nb\nnew\nc\n")
    assert changed_line_numbers(old, inserted) == {3}
    assert changed_line_numbers(old, old) == set()


def test_changed_lines_against_uses_recorded_snapshot(tmp_path):
    make_project(tmp_path)
    with _store(tmp_path) as store:
        store.refresh_digests(with_lines=True)
        recorded = store.line_hash_map()["app/calc.py"]
        modified = "def add(a, b):\n    return a + b + 1\n"
        assert store.changed_lines_against(recorded, modified) == {2}
        assert store.changed_lines_against("", modified) == set()


def test_recent_outcomes_carries_fingerprints(tmp_path):
    with _store(tmp_path) as store:
        store.record_outcomes("run1", {"t": "passed"}, {"t": 0.1}, {"t": "old"})
        store.record_outcomes("run2", {"t": "failed"}, {"t": 0.1}, {"t": "new"})
        assert store.recent_outcomes("t") == [("failed", "new"), ("passed", "old")]