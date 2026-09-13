# Changelog

All notable changes to this project.  The project follows the sprint structure of
CS5351: three sprints of four weeks.

## [Unreleased]

### Sprint 1 — walking skeleton (2026-09-14)

* Added `pytest-risktest` plugin: opt-in `--risktest` flag, `--risktest-policy`
  (`off`, `fast`, `balanced`, `safe`), selection and risk ordering in
  `pytest_collection_modifyitems`.
* Added PEP 669 based dependency monitor (`monitor.py`) with file granularity,
  optional line granularity, and a deferred per-code-object line strategy.
* Added static import graph and transitive closure (`graph.py`).
* Added SQLite store with change detection, dependency fingerprints, bounded
  outcome history and staleness pruning (`store.py`).
* Added evidence fusion, policies, stop rules and explainable reasons
  (`selector.py`).
* Added differential flakiness detection and the `flaky-check` command
  (`flaky.py`, `cli.py`).
* Added JSON/Markdown/HTML run reports with inline SVG charts (`report.py`).
* Added 96 tests (unit + ten end-to-end plugin tests in subprocesses).
* Added the evaluation harness, subject generator, mutation operators and three
  experiments (tracing strategies, untraced paths, self-hosted target).
* Added the engineering documentation set (problem statement, requirements,
  ADRs, evaluation contract, risk register, coding-agent contract, traceability,
  sprint plans, burndown) and the CI workflow.

