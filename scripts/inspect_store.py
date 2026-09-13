"""Diagnostic helper: look inside the dependency store.

This is the tool a developer (or a reviewer) uses when a selection looks
surprising.  It answers three questions without reading any code:

* what does the tool know right now?  (``--summary``)
* which tests depend on a given file?  (``--file app/core/mathx.py``)
* which files does a given test depend on?  (``--test tests/test_billing.py`` or a
  node id fragment)

Usage::

    python scripts/inspect_store.py --root benchmark/subjects/subject_01 --summary
    python scripts/inspect_store.py --root benchmark/subjects/subject_01 --file app/core/mathx.py
    python scripts/inspect_store.py --root . --test test_selector
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_STORE = ".risktest/deps.sqlite3"


def connect(root: Path, store: str) -> sqlite3.Connection:
    path = Path(store)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise SystemExit(
            f"no store at {path}\n"
            "run a warm-up first, e.g.\n"
            "  python -m pytest tests -p pytest_risktest.plugin --risktest "
            "--risktest-policy=off"
        )
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def show_summary(connection: sqlite3.Connection) -> None:
    def scalar(query: str, *args: object) -> int:
        return int(connection.execute(query, args).fetchone()[0] or 0)

    print(f"files tracked        : {scalar('SELECT COUNT(*) FROM files')}")
    print(f"tests tracked        : {scalar('SELECT COUNT(*) FROM tests')}")
    print(f"tests with traces    : {scalar('SELECT COUNT(DISTINCT nodeid) FROM test_deps')}")
    print(f"dependency edges     : {scalar('SELECT COUNT(*) FROM test_deps')}")
    print(f"flaky suspects       : {scalar('SELECT COUNT(*) FROM tests WHERE flaky = 1')}")
    print(f"always-run tests     : {scalar('SELECT COUNT(*) FROM tests WHERE always_run = 1')}")
    print(f"recorded outcomes    : {scalar('SELECT COUNT(*) FROM outcomes')}")
    print()
    print("most depended-on files:")
    rows = connection.execute(
        "SELECT path, COUNT(DISTINCT nodeid) AS tests FROM test_deps "
        "GROUP BY path ORDER BY tests DESC, path LIMIT 15"
    ).fetchall()
    for row in rows:
        print(f"  {row['tests']:>4} tests  {row['path']}")


def show_file(connection: sqlite3.Connection, needle: str) -> None:
    rows = connection.execute(
        "SELECT nodeid, lines FROM test_deps WHERE path LIKE ? ORDER BY nodeid",
        (f"%{needle}%",),
    ).fetchall()
    print(f"tests that exercised a file matching {needle!r}: {len(rows)}")
    for row in rows:
        line_count = len([part for part in row["lines"].split(",") if part])
        suffix = f"  ({line_count} lines)" if line_count else ""
        print(f"  {row['nodeid']}{suffix}")


def show_test(connection: sqlite3.Connection, needle: str) -> None:
    rows = connection.execute(
        "SELECT nodeid, path, lines FROM test_deps WHERE nodeid LIKE ? ORDER BY nodeid, path",
        (f"%{needle}%",),
    ).fetchall()
    if not rows:
        print(f"no recorded dependencies for a test matching {needle!r}")
        return
    print(f"dependencies of tests matching {needle!r}:")
    current = None
    for row in rows:
        if row["nodeid"] != current:
            current = row["nodeid"]
            print(f"\n{current}")
        line_count = len([part for part in row["lines"].split(",") if part])
        suffix = f"  ({line_count} lines)" if line_count else ""
        print(f"  {row['path']}{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root (default: .)")
    parser.add_argument("--store", default=DEFAULT_STORE, help="store path relative to --root")
    parser.add_argument("--summary", action="store_true", help="show what the tool knows")
    parser.add_argument("--file", default="", help="which tests depend on this file?")
    parser.add_argument("--test", default="", help="which files does this test depend on?")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    connection = connect(root, args.store)
    try:
        if not (args.summary or args.file or args.test):
            args.summary = True
        if args.summary:
            show_summary(connection)
        if args.file:
            print()
            show_file(connection, args.file)
        if args.test:
            print()
            show_test(connection, args.test)
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
