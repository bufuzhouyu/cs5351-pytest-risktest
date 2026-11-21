# Release v0.1.0

- Date: 2026-11-21
- Commit: `63eaea8` (`ci: install pytest before running tests`)
- Repository: https://github.com/bufuzhouyu/cs5351-pytest-risktest
- Tag: `v0.1.0`
- Test evidence:
  - Local: `python -m pytest tests -q` → 99 passed
  - GitHub Actions: 5 of 5 checks green
    - tests (Python 3.12) on Ubuntu and Windows
    - tests (Python 3.13) on Ubuntu and Windows
    - benchmark smoke test

## Included

- Test selection, risk ordering and flakiness triage
- PEP 669 dependency monitor, SQLite store and static import graph
- Explainable policies with stop rules, always-run set and `risktest_always`
- Benchmark harness, verified mutations and evaluation results
- Ten-slide offline presentation deck, timed script and live demo

## Known limitations

- Line granularity is opt-in and can be expensive on CPU-bound suites.
- Tests that cross a process boundary must use `@pytest.mark.risktest_always`.
- Wall-clock savings on small suites are limited by interpreter start-up.

## Links

- Actions: https://github.com/bufuzhouyu/cs5351-pytest-risktest/actions
- Evaluation summary: `benchmark/results/summary.md`
- Report draft: `docs/report/report-draft.md`
