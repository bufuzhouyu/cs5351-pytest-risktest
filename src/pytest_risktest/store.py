"""SQLite-backed persistence for dependency traces, test history and file digests.

Design notes
------------
* One file, one connection, WAL journal: the store must survive an interrupted
  test run (``Ctrl-C``, crash) without losing the traces collected so far, and it
  must not slow the suite down (NFR-1/NFR-3).
* Digests are cached behind ``(size, mtime_ns)`` so a full project rescan costs a
  ``stat`` per file instead of a hash per file.
* History is pruned to a bounded window per test, keeping the database small for
  long-lived suites (NFR-3).
"""

from __future__ import annotations

import difflib
import hashlib
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .graph import iter_python_files

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS files (
    path     TEXT PRIMARY KEY,
    digest   TEXT NOT NULL,
    size     INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    kind     TEXT NOT NULL DEFAULT 'py',
    line_hashes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS test_deps (
    nodeid TEXT NOT NULL,
    path   TEXT NOT NULL,
    lines  TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (nodeid, path)
);
CREATE TABLE IF NOT EXISTS tests (
    nodeid         TEXT PRIMARY KEY,
    fingerprint    TEXT,
    last_status    TEXT,
    last_run_ts    REAL,
    n_runs         INTEGER NOT NULL DEFAULT 0,
    n_failures     INTEGER NOT NULL DEFAULT 0,
    flaky          INTEGER NOT NULL DEFAULT 0,
    last_failed_ts REAL,
    always_run     INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS outcomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT NOT NULL,
    nodeid      TEXT NOT NULL,
    status      TEXT NOT NULL,
    duration    REAL,
    fingerprint TEXT,
    ts          REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_outcomes_nodeid ON outcomes (nodeid, id DESC);
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    ts          REAL NOT NULL,
    policy      TEXT,
    granularity TEXT,
    selected    INTEGER,
    total       INTEGER,
    failed      INTEGER,
    duration    REAL
);
"""

CONFIG_FILENAMES = (
    "pyproject.toml",
    "setup.cfg",
    "pytest.ini",
    "tox.ini",
    "requirements.txt",
    "requirements-dev.txt",
)

OUTCOME_WINDOW = 20  # outcomes kept per test


@dataclass
class TestState:
    nodeid: str
    last_status: Optional[str]
    n_runs: int
    n_failures: int
    flaky: bool
    always_run: bool
    last_failed_ts: Optional[float]
    fingerprint: Optional[str]

    @property
    def failure_rate(self) -> float:
        return self.n_failures / self.n_runs if self.n_runs else 0.0

    @property
    def failed_last_run(self) -> bool:
        return self.last_status == "failed"


@dataclass
class ChangeSet:
    changed: List[str]
    added: List[str]
    removed: List[str]
    config_changed: List[str]

    @property
    def is_empty(self) -> bool:
        return not (self.changed or self.added or self.removed or self.config_changed)

    @property
    def requires_full_run(self) -> bool:
        """A change to build/test configuration invalidates the dependency model."""
        return bool(self.config_changed)


def digest_bytes(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=16).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def hash_lines(text: str) -> List[str]:
    """Per-line fingerprints, used for line-granularity change detection."""
    return [
        hashlib.blake2b(line.encode("utf-8", errors="replace"), digest_size=8).hexdigest()
        for line in text.splitlines()
    ]


def changed_line_numbers(old_hashes: Sequence[str], new_hashes: Sequence[str]) -> Set[int]:
    """1-based line numbers of ``new_hashes`` that differ from ``old_hashes``.

    A pure-Python LCS diff (``difflib``) is enough here: it only runs for files
    whose content digest already changed.
    """
    changed: Set[int] = set()
    matcher = difflib.SequenceMatcher(None, list(old_hashes), list(new_hashes), autojunk=False)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            changed.update(range(j1 + 1, j2 + 1))
        else:  # replace / delete
            changed.update(range(j1 + 1, max(j2, j1 + 1) + 1))
    return changed


def dependency_fingerprint(deps: Dict[str, Set[int]], digests: Dict[str, str]) -> str:
    """Stable hash of *what a test depended on*.

    Two runs that observe the same files with the same content produce the same
    fingerprint, which is what makes differential flakiness detection possible:
    same fingerprint + different outcome == the test is not deterministic.
    """
    accumulator = hashlib.blake2b(digest_size=16)
    for path in sorted(deps):
        accumulator.update(path.encode("utf-8"))
        accumulator.update(b"\0")
        accumulator.update((digests.get(path) or "?").encode("ascii"))
        accumulator.update(b"\0")
        accumulator.update(",".join(str(line) for line in sorted(deps[path])).encode("ascii"))
        accumulator.update(b"\1")
    return accumulator.hexdigest()


def _encode_lines(lines: Iterable[int]) -> str:
    return ",".join(str(line) for line in sorted(lines))


def _decode_lines(raw: str) -> Set[int]:
    if not raw:
        return set()
    return {int(part) for part in raw.split(",") if part}


class Store:
    """Persistence layer.  All methods are synchronous and best-effort."""

    def __init__(self, path: Path | str, root: Path | str = ".") -> None:
        self.path = Path(path)
        self.root = Path(root).resolve()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(SCHEMA)

    # ------------------------------------------------------------ life cycle
    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # pragma: no cover
            pass

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------- file state
    def _is_config(self, rel: str) -> bool:
        return Path(rel).name in CONFIG_FILENAMES and not rel.endswith(".py")

    def refresh_digests(self, extra_files: Sequence[Path] = (), with_lines: bool = False) -> None:
        """Re-hash files whose ``(size, mtime_ns)`` changed since the last run."""
        previous_lines = {
            row["path"]: row["line_hashes"]
            for row in self._conn.execute("SELECT path, line_hashes FROM files")
        }
        stored = {
            row["path"]: (row["size"], row["mtime_ns"], row["digest"])
            for row in self._conn.execute("SELECT path, size, mtime_ns, digest FROM files")
        }
        seen: Set[str] = set()
        candidates: List[Tuple[str, Path, str]] = []
        for path in iter_python_files(self.root):
            rel = path.relative_to(self.root).as_posix()
            candidates.append((rel, path, "py"))
        for name in CONFIG_FILENAMES:
            candidate = self.root / name
            if candidate.is_file():
                candidates.append((name, candidate, "config"))
        for path in extra_files:
            path = Path(path)
            if path.is_file():
                rel = os.path.relpath(path, self.root).replace(os.sep, "/")
                candidates.append((rel, path, "py"))

        rows = []
        now = time.time()
        for rel, path, kind in candidates:
            seen.add(rel)
            try:
                stat = path.stat()
            except OSError:
                continue
            previous = stored.get(rel)
            if previous and previous[0] == stat.st_size and previous[1] == stat.st_mtime_ns:
                digest = previous[2]
            else:
                try:
                    digest = digest_file(path)
                except OSError:
                    continue
            line_hashes = previous_lines.get(rel, "")
            if with_lines and kind == "py":
                try:
                    line_hashes = ",".join(
                        hash_lines(path.read_text(encoding="utf-8", errors="replace"))
                    )
                except OSError:
                    line_hashes = previous_lines.get(rel, "")
            rows.append((rel, digest, stat.st_size, stat.st_mtime_ns, kind, line_hashes))
        with self._conn:
            # A temp table avoids SQLite's parameter-count limit on large trees.
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS seen_paths(path TEXT PRIMARY KEY)")
            self._conn.execute("DELETE FROM seen_paths")
            self._conn.executemany(
                "INSERT OR IGNORE INTO seen_paths(path) VALUES (?)", [(path,) for path in seen]
            )
            self._conn.execute("DELETE FROM files WHERE path NOT IN (SELECT path FROM seen_paths)")
            self._conn.executemany(
                "INSERT INTO files(path, digest, size, mtime_ns, kind, line_hashes) "
                "VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(path) DO UPDATE SET digest=excluded.digest, size=excluded.size, "
                "mtime_ns=excluded.mtime_ns, kind=excluded.kind, "
                "line_hashes=CASE WHEN excluded.line_hashes = '' THEN files.line_hashes "
                "                 ELSE excluded.line_hashes END",
                rows,
            )
            self._conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('scan_ts', ?)", (str(now),))

    def line_hash_map(self) -> Dict[str, str]:
        """Recorded per-line fingerprints, keyed by relative path."""
        return {
            row["path"]: row["line_hashes"]
            for row in self._conn.execute("SELECT path, line_hashes FROM files")
            if row["line_hashes"]
        }

    @staticmethod
    def changed_lines_against(recorded_raw: str, new_text: str) -> Set[int]:
        """Line numbers that changed relative to a previously recorded snapshot."""
        if not recorded_raw:
            return set()
        return changed_line_numbers(recorded_raw.split(","), hash_lines(new_text))

    def file_digests(self, kind: str = "py") -> Dict[str, str]:
        return {
            row["path"]: row["digest"]
            for row in self._conn.execute("SELECT path, digest FROM files WHERE kind = ?", (kind,))
        }

    # ---------------------------------------------------------------- traces
    def record_test_dependencies(
        self, nodeid: str, deps: Dict[str, Set[int]], fingerprint: str
    ) -> None:
        rows = [(nodeid, path, _encode_lines(lines)) for path, lines in deps.items()]
        with self._conn:
            self._conn.execute("DELETE FROM test_deps WHERE nodeid = ?", (nodeid,))
            if rows:
                self._conn.executemany(
                    "INSERT INTO test_deps(nodeid, path, lines) VALUES (?,?,?)", rows
                )
            self._conn.execute(
                "INSERT INTO tests(nodeid, fingerprint) VALUES (?, ?) "
                "ON CONFLICT(nodeid) DO UPDATE SET fingerprint=excluded.fingerprint",
                (nodeid, fingerprint),
            )

    def dependencies_of(self, nodeid: str) -> Dict[str, Set[int]]:
        result: Dict[str, Set[int]] = {}
        for row in self._conn.execute(
            "SELECT path, lines FROM test_deps WHERE nodeid = ?", (nodeid,)
        ):
            result[row["path"]] = _decode_lines(row["lines"])
        return result

    def tests_touching(self, paths: Iterable[str]) -> Dict[str, Set[str]]:
        """Reverse index: ``path -> {nodeid}`` restricted to ``paths``."""
        wanted = list(dict.fromkeys(paths))
        result: Dict[str, Set[str]] = {}
        chunk = 500
        for start in range(0, len(wanted), chunk):
            batch = wanted[start : start + chunk]
            placeholders = ",".join("?" * len(batch))
            query = f"SELECT path, nodeid FROM test_deps WHERE path IN ({placeholders})"
            for row in self._conn.execute(query, tuple(batch)):
                result.setdefault(row["path"], set()).add(row["nodeid"])
        return result

    def known_tests(self) -> Set[str]:
        return {row["nodeid"] for row in self._conn.execute("SELECT nodeid FROM tests")}

    def line_hits(self, nodeid: str, path: str) -> Set[int]:
        row = self._conn.execute(
            "SELECT lines FROM test_deps WHERE nodeid = ? AND path = ?", (nodeid, path)
        ).fetchone()
        return _decode_lines(row["lines"]) if row else set()

    def prune_tests(self, keep: Iterable[str]) -> int:
        keep_set = set(keep)
        existing = self.known_tests()
        stale = existing - keep_set
        if not stale:
            return 0
        with self._conn:
            for nodeid in stale:
                self._conn.execute("DELETE FROM test_deps WHERE nodeid = ?", (nodeid,))
                self._conn.execute("DELETE FROM outcomes WHERE nodeid = ?", (nodeid,))
                self._conn.execute("DELETE FROM tests WHERE nodeid = ?", (nodeid,))
        return len(stale)

    # ------------------------------------------------------------- outcomes
    def record_outcomes(
        self,
        run_id: str,
        outcomes: Dict[str, str],
        durations: Dict[str, float],
        fingerprints: Dict[str, str],
    ) -> None:
        ts = time.time()
        outcome_rows = [
            (run_id, nodeid, status, durations.get(nodeid), fingerprints.get(nodeid), ts)
            for nodeid, status in outcomes.items()
        ]
        with self._conn:
            self._conn.executemany(
                "INSERT INTO outcomes(run_id, nodeid, status, duration, fingerprint, ts) "
                "VALUES (?,?,?,?,?,?)",
                outcome_rows,
            )
            for nodeid, status in outcomes.items():
                failed = 1 if status == "failed" else 0
                self._conn.execute(
                    "INSERT INTO tests(nodeid, last_status, last_run_ts, n_runs, n_failures, "
                    "                   last_failed_ts, fingerprint) "
                    "VALUES (?,?,?,1,?,?,?) "
                    "ON CONFLICT(nodeid) DO UPDATE SET "
                    "  last_status=excluded.last_status, last_run_ts=excluded.last_run_ts, "
                    "  n_runs=tests.n_runs+1, n_failures=tests.n_failures+excluded.n_failures, "
                    "  last_failed_ts=CASE WHEN excluded.last_status='failed' THEN excluded.last_failed_ts "
                    "                      ELSE tests.last_failed_ts END, "
                    "  fingerprint=COALESCE(excluded.fingerprint, tests.fingerprint)",
                    (
                        nodeid,
                        status,
                        ts,
                        failed,
                        ts if failed else None,
                        fingerprints.get(nodeid),
                    ),
                )
            for nodeid in outcomes:
                self._conn.execute(
                    "DELETE FROM outcomes WHERE nodeid = ? AND id NOT IN "
                    "(SELECT id FROM outcomes WHERE nodeid = ? ORDER BY id DESC LIMIT ?)",
                    (nodeid, nodeid, OUTCOME_WINDOW),
                )

    def record_run_summary(
        self,
        run_id: str,
        policy: str,
        granularity: str,
        selected: int,
        total: int,
        failed: int,
        duration: float,
    ) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO runs(run_id, ts, policy, granularity, selected, total, "
                "failed, duration) VALUES (?,?,?,?,?,?,?,?)",
                (run_id, time.time(), policy, granularity, selected, total, failed, duration),
            )

    def test_states(self) -> Dict[str, TestState]:
        states: Dict[str, TestState] = {}
        for row in self._conn.execute(
            "SELECT nodeid, last_status, n_runs, n_failures, flaky, always_run, "
            "       last_failed_ts, fingerprint FROM tests"
        ):
            states[row["nodeid"]] = TestState(
                nodeid=row["nodeid"],
                last_status=row["last_status"],
                n_runs=row["n_runs"],
                n_failures=row["n_failures"],
                flaky=bool(row["flaky"]),
                always_run=bool(row["always_run"]),
                last_failed_ts=row["last_failed_ts"],
                fingerprint=row["fingerprint"],
            )
        return states

    def recent_statuses(self, nodeid: str, limit: int = 5) -> List[str]:
        return [
            row["status"]
            for row in self._conn.execute(
                "SELECT status FROM outcomes WHERE nodeid = ? ORDER BY id DESC LIMIT ?",
                (nodeid, limit),
            )
        ]

    def mark_flaky(self, nodeids: Iterable[str], value: bool = True) -> int:
        ids = list(nodeids)
        if not ids:
            return 0
        with self._conn:
            self._conn.executemany(
                "UPDATE tests SET flaky = ? WHERE nodeid = ?",
                [(1 if value else 0, nodeid) for nodeid in ids],
            )
        return len(ids)

    def set_always_run(self, nodeid: str, value: bool = True) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO tests(nodeid, always_run) VALUES (?,?) "
                "ON CONFLICT(nodeid) DO UPDATE SET always_run=excluded.always_run",
                (nodeid, 1 if value else 0),
            )

    # ---------------------------------------------------------------- misc
    def set_meta(self, key: str, value: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?,?)", (key, value)
            )

    def get_meta(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def summary(self) -> Dict[str, object]:
        def scalar(query: str, *args: object) -> int:
            row = self._conn.execute(query, args).fetchone()
            return int(row[0] or 0)

        last_run = self._conn.execute(
            "SELECT run_id, ts, policy, granularity, selected, total, failed, duration "
            "FROM runs ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        return {
            "files": scalar("SELECT COUNT(*) FROM files"),
            "tests": scalar("SELECT COUNT(*) FROM tests"),
            "tests_with_deps": scalar("SELECT COUNT(DISTINCT nodeid) FROM test_deps"),
            "dependency_edges": scalar("SELECT COUNT(*) FROM test_deps"),
            "flaky_tests": scalar("SELECT COUNT(*) FROM tests WHERE flaky = 1"),
            "outcomes": scalar("SELECT COUNT(*) FROM outcomes"),
            "last_run": dict(last_run) if last_run else None,
            "scan_ts": self.get_meta("scan_ts"),
        }
