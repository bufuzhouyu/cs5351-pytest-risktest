"""pytest-risktest -- risk-aware test selection, prioritisation and flakiness triage.

The package is intentionally import-light: pytest imports :mod:`pytest_risktest.plugin`
on every run, so heavy modules are imported lazily by the plugin and the CLI.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]

