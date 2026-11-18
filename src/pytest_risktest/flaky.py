"""Flakiness triage.

Two independent, cheap signals are combined instead of rerunning the world
(which is what tools such as *iDFlakies* do and which would defeat the purpose of
a *time saving* tool):

``differential flakiness``
    A test fails although every file it depended on is byte-identical to a run in
    which it passed.  Nothing in the code changed, so the outcome cannot be
    explained by the change under test -- the test itself is untrustworthy.

``order dependence``
    The same test set is executed twice with the *same* fingerprints but with a
    different (seeded) order: outcomes that differ are state-leakage candidates.

Both signals feed the selection policies: a flaky test is always selected, so the
tool never hides a failure behind its own skip decisions.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .store import Store

CONSISTENT_PASS = "consistent-pass"
CONSISTENT_FAIL = "consistent-fail"
ORDER_DEPENDENT = "order-dependent"
NONDETERMINISTIC = "nondeterministic"
UNKNOWN = "unknown"


def classify_pair(
    first: Dict[str, str],
    second: Dict[str, str],
    *,
    fingerprints_match: bool = True,
) -> Dict[str, str]:
    """Compare two runs of the same test set and label every test."""
    verdicts: Dict[str, str] = {}
    for nodeid in sorted(set(first) | set(second)):
        a = first.get(nodeid)
        b = second.get(nodeid)
        if a is None or b is None:
            verdicts[nodeid] = UNKNOWN
        elif a == b == "passed":
            verdicts[nodeid] = CONSISTENT_PASS
        elif a == b == "failed":
            verdicts[nodeid] = CONSISTENT_FAIL
        elif fingerprints_match:
            verdicts[nodeid] = ORDER_DEPENDENT
        else:
            verdicts[nodeid] = NONDETERMINISTIC
    return verdicts


def differential_findings(
    store: Store,
    outcomes: Dict[str, str],
    fingerprints: Dict[str, str],
    history_limit: int = 5,
) -> Dict[str, str]:
    """Detect tests whose result contradicts an identical-fingerprint history."""
    findings: Dict[str, str] = {}
    for nodeid, status in outcomes.items():
        fingerprint = fingerprints.get(nodeid)
        if not fingerprint:
            continue
        for previous_status, previous_fingerprint in store.recent_outcomes(nodeid, history_limit):
            if previous_fingerprint == fingerprint and previous_status != status:
                findings[nodeid] = NONDETERMINISTIC
                break
    return findings


def flaky_candidates(store: Store) -> List[str]:
    """Tests already flagged as flaky suspects."""
    return sorted(nodeid for nodeid, state in store.test_states().items() if state.flaky)


def summarize(verdicts: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for verdict in verdicts:
        counts[verdict] = counts.get(verdict, 0) + 1
    return dict(sorted(counts.items()))


def suspects_from_verdicts(verdicts: Dict[str, str]) -> Sequence[str]:
    return sorted(
        nodeid
        for nodeid, verdict in verdicts.items()
        if verdict in (ORDER_DEPENDENT, NONDETERMINISTIC)
    )

