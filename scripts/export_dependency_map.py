"""Export the tool's dependency knowledge as JSON.

The export contains everything needed to *replay* a selection decision outside
pytest: the observed ``test -> files`` map, the static import graph, and the run
history.  It is used by the interactive explainer of the project and by anyone who
wants to inspect the evidence in a spreadsheet.

Usage::

    python scripts/export_dependency_map.py --root benchmark/subjects/subject_01 \
        --output benchmark/results/dependency-map.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from pytest_risktest.graph import static_imports  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root that owns the store")
    parser.add_argument("--store", default=".risktest/deps.sqlite3")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    store = Path(args.store)
    if not store.is_absolute():
        store = root / store
    if not store.exists():
        raise SystemExit(f"no store at {store}; run a warm-up first")

    connection = sqlite3.connect(str(store))
    connection.row_factory = sqlite3.Row
    try:
        tests: dict[str, list[str]] = {}
        for row in connection.execute("SELECT nodeid, path FROM test_deps ORDER BY nodeid, path"):
            tests.setdefault(row["nodeid"], []).append(row["path"])
        history = {
            row["nodeid"]: {
                "last_status": row["last_status"],
                "runs": row["n_runs"],
                "failures": row["n_failures"],
                "flaky": bool(row["flaky"]),
                "always_run": bool(row["always_run"]),
            }
            for row in connection.execute(
                "SELECT nodeid, last_status, n_runs, n_failures, flaky, always_run FROM tests"
            )
        }
    finally:
        connection.close()

    imports = {
        path: sorted(targets) for path, targets in sorted(static_imports(root).items())
    }
    payload = {
        "root": root.name,
        "tests": tests,
        "imports": imports,
        "history": history,
        "test_count": len(tests),
        "edge_count": sum(len(files) for files in tests.values()),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    print(
        f"{output} written: {payload['test_count']} tests, "
        f"{payload['edge_count']} dependency edges, {len(imports)} files in the import graph"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

