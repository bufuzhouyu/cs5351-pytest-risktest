"""Evaluation metrics.

The metric set is frozen in ``docs/05-evaluation-contract.md`` *before* any
comparison is run:

* ``APFD``      -- average percentage of faults detected by the produced order;
* ``recall``    -- share of the ground-truth failing tests that were executed
                   (this is the safety metric: 1.0 means no failure was hidden);
* ``skip_rate`` -- share of the suite that was not executed;
* ``time_saved``-- wall-clock saving of the selected run vs. the full run;
* ``overhead``  -- cost of observing the suite when nothing is skipped.
"""

from __future__ import annotations

import math
import statistics
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set


def apfd(order: Sequence[str], failing: Iterable[str], universe: Optional[Sequence[str]] = None) -> float:
    """Average Percentage of Faults Detected.

    Higher is better; ``1.0`` is the limit as the suite grows, and for ``m``
    faults among ``n`` tests the best achievable value is ``1 - m / (2n)``.

    ``universe`` is the full test set; failing tests that were never executed
    count as detected last, which penalises unsafe selection instead of hiding it.
    """
    failing_set = {test for test in failing if test}
    if not failing_set:
        return float("nan")
    positions: Dict[str, int] = {test: index + 1 for index, test in enumerate(order)}
    size = len(universe) if universe else len(order)
    if size == 0:
        return float("nan")
    total = 0.0
    for test in failing_set:
        total += positions.get(test, size + 1)
    m = len(failing_set)
    return 1.0 - total / (size * m) + 1.0 / (2.0 * size)


def recall(executed: Iterable[str], failing: Iterable[str]) -> float:
    """Fraction of the ground-truth failures that the selection actually ran."""
    failing_set = {test for test in failing if test}
    if not failing_set:
        return 1.0
    executed_set = set(executed)
    return len(executed_set & failing_set) / len(failing_set)


def missed_failures(executed: Iterable[str], failing: Iterable[str]) -> List[str]:
    executed_set = set(executed)
    return sorted(test for test in failing if test not in executed_set)


def skip_rate(executed: Iterable[str], universe: Iterable[str]) -> float:
    universe_list = list(universe)
    if not universe_list:
        return 0.0
    return 1.0 - len(set(executed) & set(universe_list)) / len(universe_list)


def time_saved(full_seconds: float, selected_seconds: float) -> float:
    if full_seconds <= 0:
        return float("nan")
    return (full_seconds - selected_seconds) / full_seconds


def overhead_pct(baseline_seconds: float, traced_seconds: float) -> float:
    if baseline_seconds <= 0:
        return float("nan")
    return (traced_seconds - baseline_seconds) / baseline_seconds * 100.0


def summarize(values: Iterable[float], drop_nan: bool = True) -> Dict[str, float]:
    data = [value for value in values if not (drop_nan and isinstance(value, float) and math.isnan(value))]
    if not data:
        return {"n": 0, "mean": float("nan"), "median": float("nan"), "min": float("nan"), "max": float("nan")}
    return {
        "n": len(data),
        "mean": statistics.fmean(data),
        "median": statistics.median(data),
        "min": min(data),
        "max": max(data),
    }


def aggregate_rows(rows: Sequence[Mapping[str, float]]) -> Dict[str, Dict[str, float]]:
    """Aggregate a benchmark table into per-metric statistics."""
    if not rows:
        return {}
    keys = [key for key in rows[0] if key not in ("subject", "mutation", "policy")]
    return {
        key: summarize([row[key] for row in rows if isinstance(row.get(key), (int, float))])
        for key in keys
    }
