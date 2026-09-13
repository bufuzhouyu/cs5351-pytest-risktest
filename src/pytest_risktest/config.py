"""Configuration model for the plugin.

The runtime behaviour is fully described by two things:

* the *policy* (how much of the dependency closure is considered), and
* the *traces* (which dynamic dependencies were observed).

Policies are deliberately explicit rather than a set of independent flags so that
the trade-off documented in ``docs/04-architecture.md`` stays auditable: each
policy maps onto one point of the recall/precision curve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

DEFAULT_STORE_PATH = ".risktest/deps.sqlite3"
DEFAULT_REPORT_PATH = ".risktest/last-run.json"


@dataclass(frozen=True)
class Policy:
    """A named, auditable selection policy."""

    name: str
    select: bool
    transitive_depth: Optional[int]
    include_always: bool
    description: str

    @property
    def depth_label(self) -> str:
        if self.transitive_depth is None:
            return "closure"
        return str(self.transitive_depth)


POLICIES: Dict[str, Policy] = {
    "off": Policy(
        name="off",
        select=False,
        transitive_depth=0,
        include_always=False,
        description="No selection; the suite is executed in full (trace-only).",
    ),
    "fast": Policy(
        name="fast",
        select=True,
        transitive_depth=0,
        include_always=True,
        description="Only tests that dynamically executed a changed file.",
    ),
    "balanced": Policy(
        name="balanced",
        select=True,
        transitive_depth=1,
        include_always=True,
        description="Directly impacted tests plus one hop of the static import closure.",
    ),
    "safe": Policy(
        name="safe",
        select=True,
        transitive_depth=None,
        include_always=True,
        description="Full static import closure plus every always-run test.",
    ),
}

GRANULARITIES = ("file", "line")
LINE_STRATEGIES = ("local", "global")
ORDERINGS = ("risk", "original", "shuffle")
CHANGE_MODES = ("auto", "hash", "git", "none")


@dataclass
class RiskTestSettings:
    """Resolved plugin settings for one pytest session."""

    enabled: bool = False
    policy: Policy = field(default_factory=lambda: POLICIES["balanced"])
    granularity: str = "file"
    line_strategy: str = "local"
    ordering: str = "risk"
    change_mode: str = "auto"
    base_ref: str = "HEAD"
    store_path: str = DEFAULT_STORE_PATH
    report_path: Optional[str] = DEFAULT_REPORT_PATH
    shuffle_seed: Optional[int] = None
    max_deselect_pct: float = 90.0
    min_selected: int = 1
    trace_only: bool = False
    verbose: bool = False

    @property
    def selecting(self) -> bool:
        return self.enabled and self.policy.select and not self.trace_only


def policy_from_name(name: str) -> Policy:
    try:
        return POLICIES[name]
    except KeyError:  # pragma: no cover - guarded by argparse choices
        raise ValueError(f"unknown policy {name!r}; expected one of {sorted(POLICIES)}") from None
