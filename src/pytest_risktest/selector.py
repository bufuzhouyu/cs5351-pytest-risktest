"""The decision engine: which tests must run, and in which order.

Two evidence sources are fused:

``dynamic`` (observed)
    ``test -> files`` collected by :mod:`pytest_risktest.monitor` in earlier runs.
    High precision, zero recall guarantees for code paths never executed before.

``static`` (derived)
    reverse import closure from :mod:`pytest_risktest.graph`.  Lower precision,
    covers files a test could start to use after the change.

Everything that cannot be justified as "cannot be affected" is selected.  The
policy names in :mod:`pytest_risktest.config` make that trade-off explicit, and
``safe`` is the policy the report recommends for CI.
"""

from __future__ import annotations

import math
import random
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .config import Policy
from .graph import ImportGraph
from .store import ChangeSet, Store, TestState

REASON_ORDER = (
    "changed-dependency",
    "changed-line",
    "transitive-dependency",
    "unknown-dependency",
    "new-test",
    "previous-failure",
    "flaky-suspect",
    "always-run",
)


@dataclass
class SelectionPlan:
    policy: str
    granularity: str
    total_tests: int
    selected: List[str]
    deselected: List[str]
    reasons: Dict[str, str]
    risk: Dict[str, float]
    change: ChangeSet
    fallback: Optional[str] = None
    line_hits: Dict[str, int] = field(default_factory=dict)

    @property
    def selected_count(self) -> int:
        return len(self.selected)

    @property
    def deselected_count(self) -> int:
        return len(self.deselected)

    @property
    def skip_rate(self) -> float:
        return self.deselected_count / self.total_tests if self.total_tests else 0.0

    def reason_histogram(self) -> Dict[str, int]:
        histogram: Dict[str, int] = {}
        for reason in self.reasons.values():
            histogram[reason] = histogram.get(reason, 0) + 1
        return dict(sorted(histogram.items(), key=lambda item: (-item[1], item[0])))

    def to_dict(self) -> Dict[str, object]:
        return {
            "policy": self.policy,
            "granularity": self.granularity,
            "total_tests": self.total_tests,
            "selected": self.selected_count,
            "deselected": self.deselected_count,
            "skip_rate": round(self.skip_rate, 4),
            "fallback": self.fallback,
            "changed_files": self.change.changed,
            "added_files": self.change.added,
            "removed_files": self.change.removed,
            "config_changed": self.change.config_changed,
            "reason_histogram": self.reason_histogram(),
        }


# --------------------------------------------------------------------- change
def git_changed_files(root: Path, base_ref: str) -> Optional[List[str]]:
    """Return files changed according to git, or ``None`` when unavailable."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return [line.strip().replace("\\", "/") for line in out.stdout.splitlines() if line.strip()]


def resolve_change(
    store: Store,
    root: Path,
    mode: str,
    base_ref: str,
    current_digests: Dict[str, str],
    previous_digests: Dict[str, str],
    previous_config: Dict[str, str],
    current_config: Dict[str, str],
) -> ChangeSet:
    """Determine the change set for this run.

    ``mode`` is one of ``hash`` (default, works without git), ``git``, ``auto``
    (git when the repository is clean enough, else hash) or ``none``.
    """
    if mode == "none":
        return ChangeSet([], [], [], [])
    if mode in ("git", "auto"):
        files = git_changed_files(root, base_ref)
        if files is not None and mode == "git":
            config = [f for f in files if Path(f).name in {"pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg"}]
            py_files = [f for f in files if f.endswith(".py") and f not in config]
            return ChangeSet(changed=py_files, added=[], removed=[], config_changed=config)
    changed = [p for p, d in current_digests.items() if p in previous_digests and previous_digests[p] != d]
    added = [p for p in current_digests if p not in previous_digests]
    removed = [p for p in previous_digests if p not in current_digests]
    config_changed = [p for p, d in current_config.items() if previous_config.get(p) != d]
    return ChangeSet(
        changed=sorted(changed), added=sorted(added), removed=sorted(removed),
        config_changed=sorted(config_changed),
    )


# ------------------------------------------------------------------ selection
def risk_score(
    state: Optional[TestState], reason: str, line_hits: int, changed_lines: int
) -> float:
    """Heuristic priority for orderings (higher runs first).

    The weights encode the project's evaluation contract: recent failures and
    known flakiness are the strongest predictors of another failure, followed by
    how much of the changed code the test exercises.
    """
    score = 0.0
    if state is not None:
        if state.failed_last_run:
            score += 3.0
        if state.flaky:
            score += 2.0
        score += min(state.failure_rate, 1.0)
    score += 1.5 if reason == "changed-dependency" else 0.0
    score += 1.0 if reason == "changed-line" else 0.0
    score += 0.5 if reason == "transitive-dependency" else 0.0
    score += 0.4 if reason in ("previous-failure", "always-run", "new-test") else 0.0
    if changed_lines > 0 and line_hits > 0:
        score += 0.5 * min(1.0, line_hits / changed_lines)
    return round(score, 4)


def plan_selection(
    all_tests: Sequence[str],
    store: Store,
    graph: ImportGraph,
    policy: Policy,
    change: ChangeSet,
    granularity: str = "file",
    changed_lines: Optional[Dict[str, Set[int]]] = None,
    max_deselect_pct: float = 90.0,
    min_selected: int = 1,
    forced: Iterable[str] = (),
) -> SelectionPlan:
    """Decide which tests to run for ``change`` under ``policy``."""
    all_tests = list(all_tests)
    states = store.test_states()
    known = store.known_tests()
    changed_lines = changed_lines or {}
    total_changed_lines = sum(len(lines) for lines in changed_lines.values())

    reasons: Dict[str, str] = {}
    hits: Dict[str, int] = {}
    selected: Set[str] = set()

    changed_paths = [p for p in change.changed if p.endswith(".py")]
    added_paths = [p for p in change.added if p.endswith(".py")]

    if not policy.select:
        risk_all = {
            nodeid: risk_score(states.get(nodeid), "policy-off", 0, 0) for nodeid in all_tests
        }
        return SelectionPlan(
            policy=policy.name,
            granularity=granularity,
            total_tests=len(all_tests),
            selected=list(all_tests),
            deselected=[],
            reasons={nodeid: "policy-off" for nodeid in all_tests},
            risk=risk_all,
            change=change,
        )

    if change.requires_full_run:
        return SelectionPlan(
            policy=policy.name,
            granularity=granularity,
            total_tests=len(all_tests),
            selected=list(all_tests),
            deselected=[],
            reasons={nodeid: "always-run" for nodeid in all_tests},
            risk={},
            change=change,
            fallback="configuration files changed",
        )

    direct = store.tests_touching(changed_paths)
    added_direct = store.tests_touching(added_paths)

    for path, nodeids in direct.items():
        for nodeid in nodeids:
            if nodeid not in all_tests:
                continue
            lines = store.line_hits(nodeid, path) if granularity == "line" else set()
            if granularity == "line" and lines and changed_lines.get(path):
                overlap = lines & changed_lines[path]
                hits[nodeid] = len(overlap)
                reasons[nodeid] = "changed-line" if overlap else "changed-dependency"
            else:
                reasons[nodeid] = "changed-dependency"
            selected.add(nodeid)
    for _path, nodeids in added_direct.items():
        for nodeid in nodeids:
            if nodeid in all_tests:
                selected.add(nodeid)
                reasons.setdefault(nodeid, "changed-dependency")

    if policy.transitive_depth is None or policy.transitive_depth > 0:
        affected_files = graph.affected_by(changed_paths + added_paths, policy.transitive_depth)
        if affected_files:
            affected_tests = store.tests_touching(sorted(affected_files))
            for _path, nodeids in affected_tests.items():
                for nodeid in nodeids:
                    if nodeid in all_tests and nodeid not in selected:
                        selected.add(nodeid)
                        reasons[nodeid] = "transitive-dependency"

    if policy.include_always:
        for nodeid in all_tests:
            state = states.get(nodeid)
            if nodeid not in known or not store.dependencies_of(nodeid):
                selected.add(nodeid)
                reasons.setdefault(nodeid, "new-test" if nodeid not in known else "unknown-dependency")
            elif state is not None and state.always_run:
                selected.add(nodeid)
                reasons.setdefault(nodeid, "always-run")
            elif state is not None and state.flaky:
                selected.add(nodeid)
                reasons.setdefault(nodeid, "flaky-suspect")
            elif state is not None and state.failed_last_run:
                selected.add(nodeid)
                reasons.setdefault(nodeid, "previous-failure")

    for nodeid in forced:
        if nodeid in all_tests:
            selected.add(nodeid)
            reasons.setdefault(nodeid, "always-run")

    # Never distrust the model more than the stop rule allows (see docs/06-risk-register.md).
    cap = math.floor(len(all_tests) * (1.0 - max_deselect_pct / 100.0))
    if len(selected) < max(min_selected, cap) and all_tests:
        ordered = sorted(
            all_tests,
            key=lambda nodeid: (
                -(states.get(nodeid).failure_rate if states.get(nodeid) else 0.0),
                nodeid,
            ),
        )
        for nodeid in ordered:
            if len(selected) >= max(min_selected, cap):
                break
            selected.add(nodeid)
            reasons.setdefault(nodeid, "always-run")

    risk = {
        nodeid: risk_score(states.get(nodeid), reasons.get(nodeid, "unknown"), hits.get(nodeid, 0), total_changed_lines)
        for nodeid in selected
    }
    selected_list = sorted(selected, key=lambda nodeid: (-risk.get(nodeid, 0.0), nodeid))
    deselected = [nodeid for nodeid in all_tests if nodeid not in selected]
    return SelectionPlan(
        policy=policy.name,
        granularity=granularity,
        total_tests=len(all_tests),
        selected=selected_list,
        deselected=deselected,
        reasons=reasons,
        risk=risk,
        change=change,
        line_hits=hits,
    )


def order_tests(plan: SelectionPlan, ordering: str, seed: Optional[int] = None) -> List[str]:
    """Apply the requested ordering to the selected tests."""
    selected = list(plan.selected)
    if ordering == "original":
        return selected
    if ordering == "shuffle":
        rng = random.Random(seed if seed is not None else 0)
        shuffled = list(selected)
        rng.shuffle(shuffled)
        return shuffled
    return sorted(selected, key=lambda nodeid: (-plan.risk.get(nodeid, 0.0), nodeid))
