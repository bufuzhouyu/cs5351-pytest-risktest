# Requirements

Nine user stories carry the sprint scope; three non-functional requirements carry
the architectural scope.  Every story has acceptance criteria that are executable
(the test that proves it is named), and every non-functional requirement is
addressed by a design decision in `docs/04-architecture.md` with a measurement.

## User stories

| ID | Story | Acceptance criteria | Proof |
| --- | --- | --- | --- |
| US-1 | As a developer I want the tool to record which files my tests execute, so decisions can be based on evidence instead of guesses. | After a run, the store contains at least one dependency edge per executed test; a test that never touches a module has no edge to it. | `tests/test_monitor.py::test_records_files_executed_by_one_test`, `::test_dependencies_are_attributed_per_test` |
| US-2 | As a developer I want a change to trigger only the tests that exercise it. | After modifying one module, a `fast` run executes exactly the tests whose traces include that module and deselects the rest. | `tests/test_plugin_integration.py::test_changed_module_selects_only_its_tests` |
| US-3 | As a developer I want a safety net when a test's dependency could not be observed. | Tests with no recorded dependencies, new tests, previously failing tests and flaky tests are always selected. | `tests/test_selector.py::test_unknown_dependency_is_always_selected`, `::test_previous_failure_and_flaky_tests_are_kept` |
| US-4 | As a reviewer I want to see *why* each test was selected and which change caused it. | The run report contains the changed files, the selector reason histogram and the deselected list. | `tests/test_plugin_integration.py::test_warmup_run_traces_everything`, `tests/test_report.py::test_markdown_contains_key_numbers` |
| US-5 | As a release engineer I want to cap how much of the suite may be skipped. | A configuration change forces a full run; the maximum-skip stop rule and the minimum-selected rule are enforced. | `tests/test_plugin_integration.py::test_configuration_change_forces_a_full_run`, `::test_stop_rule_caps_the_skip_rate`, `tests/test_selector.py::test_stop_rule_selects_a_minimum_share_of_the_suite` |
| US-6 | As a developer I want the most likely failures to run first. | Selected tests are ordered by the documented risk score; the order is reproducible. | `tests/test_selector.py::test_risk_score_prefers_recent_failures`, `::test_order_tests_supports_all_modes` |
| US-7 | As a developer I want flaky tests to be surfaced, not silently trusted. | A test whose outcome contradicts an identical dependency fingerprint is flagged; a second, order-perturbed run is available on demand. | `tests/test_flaky.py::test_differential_findings_detects_contradicting_history`, `risktest flaky-check` |
| US-8 | As a developer I want the tool to work in my repository without extra services. | No third-party runtime dependency; works without git, network or a build server; state lives in one SQLite file. | `tests/test_cli.py`, `tests/test_plugin_integration.py::test_plugin_is_inert_without_the_flag` |
| US-9 | As a developer I want a test that cannot be traced to be excluded explicitly. | `@pytest.mark.risktest_always` forces selection regardless of policy. | `tests/test_plugin_integration.py::test_always_run_marker_overrides_selection` |

## Non-functional requirements

### NFR-1 Performance

**Requirement.** Observation must not dominate the suite: with *file*
granularity the observation overhead must stay below **20 %** of the untraced
suite runtime on a suite whose tests perform real work; *line* granularity is an
opt-in mode whose cost must be measured and documented, not assumed.

**Measured.** file: −8.5 %, −0.3 %, +7.9 % (generated subjects) and +16.7 %
(this project's own suite); line: +508 %, +532 %, +551 % (generated, CPU-bound)
and +26 % (this project's suite).  Source:
`benchmark/results/summary.md`, `benchmark/results/tracing-strategies.md`.

**Design.** ADR-1 (PEP 669 instead of a full tracer), ADR-2 (deferred local line
instrumentation), ADR-3 (file granularity as the default), ADR-4 (digest cache
behind `(size, mtime_ns)` and a single SQLite file).

### NFR-2 Reliability (safety of the skip decision)

**Requirement.** A failing test that the change caused must never be skipped:
**recall = 1.0, zero missed failures** on the frozen benchmark; the plugin must
never turn a user's red suite green, and a failure inside the tool itself must
degrade to a normal full run instead of breaking the session.

**Measured.** 36 mutation runs across four targets: minimum recall 1.000, zero
missed failures, zero false "green" outcomes
(`benchmark/results/summary.md`).  The known blind spot is measured and mitigated
rather than ignored (`benchmark/results/untraced-paths.md`).

**Design.** ADR-5 (evidence fusion and always-run set), ADR-6 (stop rules and the
`risktest_always` escape hatch), ADR-7 (defensive plugin, isolated state).

### NFR-3 Scalability and portability

**Requirement.** The tool must keep a bounded footprint on a large suite (no
unbounded growth of history), must run the same way on Windows and Linux, and
must not require network access, git, or a third-party package.

**Measured / enforced.** one SQLite file with WAL journal; outcome history is
pruned to 20 records per test (`tests/test_store.py::test_outcome_history_is_pruned`);
dependency edges are replaced per run instead of accumulating
(`::test_recording_dependencies_replaces_previous_edges`); stale tests are pruned
when they disappear from collection (`::test_prune_tests_removes_stale_entries`);
the static import scan walks the project tree once and skips `.git`, `.venv`,
`__pycache__`, `node_modules`, `build`, `dist`
(`tests/test_graph.py::test_syntax_error_file_does_not_break_scan`); the whole
experiment runs offline with no installed dependency.

## Constraints accepted by the team

* Python 3.12+ is required for `sys.monitoring`; on older interpreters the plugin
  reports the limitation instead of silently degrading
  (`tests/test_monitor.py::test_unavailable_monitor_raises_when_forced`).
* The dependency model is per file (and optionally per line), not per function:
  coarser granularity is the price for the low overhead measured in NFR-1.
* Only the instrumented interpreter is observable; process-boundary tests must
  declare themselves (US-9).

