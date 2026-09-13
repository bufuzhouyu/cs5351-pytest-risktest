# Traceability: requirement → code → test → evidence

The chain the course asks for is: an issue records the problem and acceptance
criteria, a pull request links code, tests and review discussion, and the closing
syntax connects the accepted change back to the requirement.  This table is the
current state of that chain, and it is meant to be extended line by line as the
team lands each change.

| Requirement | Code (module · symbol) | Automated proof | Evidence artefact |
| --- | --- | --- | --- |
| US-1 trace tests to files | `monitor.py` · `DependencyMonitor._on_py_start`, `store.py` · `record_test_dependencies` | `tests/test_monitor.py` (14 tests), `tests/test_store.py::test_dependency_roundtrip_and_reverse_index` | run report `store.dependency_edges` |
| US-2 select only affected tests | `selector.py` · `plan_selection`, `plugin.py` · `_apply_selection` | `tests/test_plugin_integration.py::test_changed_module_selects_only_its_tests`, `tests/test_selector.py::test_fast_policy_selects_only_directly_exercised_tests` | `benchmark/results/summary.md` (`skip_rate`) |
| US-3 safety net for unknown dependencies | `selector.py` · always-run branch | `tests/test_selector.py::test_unknown_dependency_is_always_selected`, `::test_previous_failure_and_flaky_tests_are_kept` | `reason_histogram` in every run report |
| US-4 explainable decisions | `selector.py` · `SelectionPlan.to_dict`, `report.py` | `tests/test_report.py` (9 tests), `test_plugin_integration.py::test_warmup_run_traces_everything` | `.risktest/last-run.{json,md,html}` |
| US-5 stop rules | `selector.py` · stop rule, `config.py` · `RiskTestSettings` | `test_selector.py::test_stop_rule_selects_a_minimum_share_of_the_suite`, `test_plugin_integration.py::test_stop_rule_caps_the_skip_rate`, `::test_configuration_change_forces_a_full_run` | `docs/06-risk-register.md` §Stop rules |
| US-6 risk ordering | `selector.py` · `risk_score`, `order_tests` | `test_selector.py::test_risk_score_prefers_recent_failures`, `::test_order_tests_supports_all_modes` | `APFD` columns in `benchmark/results/benchmark.csv` |
| US-7 flakiness triage | `flaky.py`, `store.py` · `dependency_fingerprint`, `cli.py` · `flaky-check` | `tests/test_flaky.py` (5 tests) | `flaky_findings` in the report; `risktest flaky-check` output |
| US-8 zero-dependency operation | `pyproject.toml` (`dependencies = []`), `cli.py`, `store.py` | `tests/test_cli.py` (6 tests) | CI workflow runs with no install step |
| US-9 escape hatch for untraceable tests | `plugin.py` · `_apply_markers`, `store.set_always_run` | `test_plugin_integration.py::test_always_run_marker_overrides_selection` | `benchmark/results/untraced-paths.md` |
| NFR-1 performance | `monitor.py` (PEP 669, local line strategy), `store.py` (digest cache) | `tests/test_monitor.py::test_measure_overhead_reports_percentage` | `benchmark/results/tracing-strategies.md`, `summary.md` §overhead |
| NFR-2 reliability | `selector.py` (always-run + stop rules), `plugin.py` (defensive hooks) | integration tests asserting failures are never hidden | `benchmark/results/benchmark.csv` (`recall`, `misses`) |
| NFR-3 scalability & portability | `store.py` (WAL, pruning), `graph.py` (single scan, skip list) | `test_store.py::test_outcome_history_is_pruned`, `::test_prune_tests_removes_stale_entries` | `risktest status` output |

## Closing syntax used in commits and pull requests

```
US-3: always select tests with unknown dependencies

Closes #12
Evidence: pytest tests/test_selector.py -q  ->  17 passed
Contract: docs/05-evaluation-contract.md unchanged
```

The status check in `.github/workflows/ci.yml` is what makes the evidence visible
at review time: a pull request that does not run the tests cannot be merged.

