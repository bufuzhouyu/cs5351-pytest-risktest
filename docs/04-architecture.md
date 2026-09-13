# Architecture

## Component view

```
                       ┌──────────────────────────── pytest session ───────────────────────────┐
   developer / CI ────► │ plugin.RiskTestController                                             │
                       │   pytest_addoption / --risktest-*                                     │
                       │   pytest_collection_modifyitems ──► selector.plan_selection ──► items  │
                       │   pytest_runtest_setup/teardown ──► monitor.DependencyMonitor          │
                       │   pytest_runtest_logreport ───────► outcomes / durations               │
                       │   pytest_sessionfinish ───────────► store + report                     │
                       └───────┬───────────────┬───────────────┬───────────────┬───────────────┘
                               │               │               │               │
                        monitor.py        graph.py         store.py        report.py
                     PEP 669 events   static import     SQLite: traces,   JSON / MD /
                     test→{file:lines} closure          history, digests  HTML + SVG
                               │               │               │
                               └──── selector.py ◄────────────┘
                                     evidence fusion, policies, risk score, stop rules
                                               │
                                     flaky.py / metrics.py
```

The CLI (`cli.py`) uses the same modules, so `risktest status|impact|report` can
never disagree with a pytest run.

## Data flow of one run

1. `pytest_collection_modifyitems` reads the previous file digests, refreshes them
   (`files.digest`, cached on `(size, mtime_ns)`), computes the change set, prunes
   stale tests, scans the static import graph and asks `plan_selection` for a plan.
2. The plan is applied: items are filtered (deselection is reported through
   `pytest_deselected`) and ordered by risk.
3. For every executed test, the monitor records `test → {file: {lines}}` while the
   test (including fixtures) runs; events are disabled between tests.
4. At session end the traces, outcomes, durations and per-test dependency
   fingerprints are persisted; differential flakiness is computed; the report is
   written in three formats.

## Data model (one file, `.risktest/deps.sqlite3`)

| Table | Key | Purpose |
| --- | --- | --- |
| `files` | `path` | content digest, size/mtime cache, per-line hashes (line granularity) |
| `test_deps` | `(nodeid, path)` | observed dependency of a test on a file (+ line numbers) |
| `tests` | `nodeid` | last status, run/failure counts, flaky flag, always-run flag, fingerprint |
| `outcomes` | `id` | bounded per-test outcome window (20) with run id, status, duration |
| `runs` | `run_id` | policy, granularity, selected/total/failed, duration |
| `meta` | `key` | scan timestamp and other bookkeeping |

## Architecture decision records

### ADR-1 — Collect dependencies with PEP 669 (`sys.monitoring`) instead of a tracer

*Options.* (a) `sys.settrace`/`coverage.Coverage`; (b) `ast`-based static analysis
only; (c) PEP 669 `sys.monitoring`; (d) import-time instrumentation of the test
process.

*Decision.* (c), with (b) as a complementary signal.

*Rationale.* A tracer pays a Python callback per executed line; `sys.monitoring`
lets the tool subscribe only to the events it needs and disables them between
tests.  Static-only analysis cannot tell which tests really exercise a file
(the generated subjects show a module-level constant that no test reads); import
instrumentation cannot see dynamic behaviour.

*Evidence.* file granularity costs −8.5 %…+16.7 %; a full tracer would sit at the
line-granularity cost measured in `benchmark/results/tracing-strategies.md`.

*Consequences.* Python ≥ 3.12 is required; the plugin must degrade explicitly on
older interpreters.  `sys.monitoring` gives exclusive tool ids, so the monitor
acquires one, reports a warning and disables itself if none is free.

### ADR-2 — Deferred, per-code-object line instrumentation

*Options.* (a) enable `LINE` globally; (b) enable `LINE` per file by pre-scanning
code objects; (c) enable `LINE` lazily from `PY_START` for code objects inside the
project and return `DISABLE` for the redundant entry event; (d) never offer line
granularity.

*Decision.* (c) as the default line strategy, (a) kept as a switch for comparison.

*Rationale.* (a) makes the whole interpreter pay, including pytest internals and
third-party Python code.  (b) needs a full module inventory before collection and
misses dynamically imported modules.  (c) pays one entry event per code object and
then only for project code, which is exactly the information the selector needs.

*Evidence.* library-bound workload: +97.2 % (global) vs −2.3 % (local);
hot-loop workload: +6046 % vs +6170 % — the strategy cannot help when the hot code
is project code, which is why file granularity stays the default
(`benchmark/results/tracing-strategies.md`).

*Consequences.* Local events are not cleared by `set_events(tool, 0)`, so the
monitor releases every instrumented code object explicitly at the end of a test
and re-arms disabled locations with `restart_events()`; this is covered by
`tests/test_monitor.py::test_line_strategy_local_keeps_working_across_tests` and
`::test_line_events_do_not_leak_outside_a_test`.

### ADR-3 — File granularity is the product default, line granularity is opt-in

*Options.* (a) line granularity only; (b) file granularity only; (c) file by
default, line on request with a measured cost warning.

*Decision.* (c).

*Rationale.* A file-level dependency answers the review question ("can this change
affect this test?") at ~0 % overhead, and the evaluation shows it is sufficient for
recall = 1.0 on 36 verified mutations.  Line granularity buys extra precision
(`changed-line` reason) at a cost that can reach two orders of magnitude on
CPU-bound tests.

*Evidence.* `benchmark/results/summary.md` (recall/skip-rate per policy),
`benchmark/results/tracing-strategies.md` (cost).

*Consequences.* The selector exposes the `changed-line` reason when line data is
available, but never depends on it.

### ADR-4 — One SQLite file with a digest cache, per-test replacement, bounded history

*Options.* (a) JSON files per test; (b) pickled dictionary; (c) SQLite (WAL) with
`(size, mtime_ns)` digest caching; (d) an external service/database.

*Decision.* (c).

*Rationale.* The store must survive interrupted runs, support reverse lookups
("which tests touch these files?") without loading everything, and stay small.
Re-hashing every file on every run would break NFR-1; `(size, mtime_ns)` gates the
hash.  Outcome history is pruned to 20 rows per test and dependency edges are
replaced per run.

*Evidence.* `tests/test_store.py` (change detection, reverse index, pruning);
observation overhead of the end-to-end plugin runs stays within NFR-1.

*Consequences.* The store is a disposable cache (`.risktest/`, git-ignored):
deleting it costs one warm-up run, never correctness.

### ADR-5 — Fuse dynamic evidence with a static closure, never trust one signal

*Options.* (a) dynamic only; (b) static only; (c) dynamic ∪ static closure, with
the always-run set on top; (d) ML-ranked selection.

*Decision.* (c), exposed as three named policies.

*Rationale.* Dynamic evidence is precise but incomplete (first run, stale traces,
process boundaries, instrumentation gaps); the static import closure is
imprecise but cannot miss a file that is *statically* reachable from a test.
Cheap-history and flakiness signals cover non-code causes.  (d) was rejected
because an unexplainable skip cannot be reviewed, and the repository has to keep
every decision auditable.

*Evidence.* `fast` (dynamic only) reaches the highest skip rate (0.854) but relies
on traces alone; `balanced`/`safe` add the closure (0.714/0.693 skip rate).  All
three kept recall at 1.0, so the extra conservatism is visible as *cost*, not as
a safety gain, on these subjects — the boundary experiment shows when it does
become a safety gain.

*Consequences.* Policies are data (`config.POLICIES`), so a team can add one
without touching the engine.

### ADR-6 — Stop rules and an explicit escape hatch

*Options.* (a) trust the model; (b) cap the skip rate and require a minimum
selection; (c) additionally provide a per-test override marker.

*Decision.* (b) + (c).

*Rationale.* "Never skip more than 90 %" and "always run at least one test" bound
the blast radius of a wrong model or a broken trace; the marker covers the cases
that are structurally invisible (process boundaries).

*Evidence.* `tests/test_selector.py::test_stop_rule_selects_a_minimum_share_of_the_suite`,
`tests/test_plugin_integration.py::test_stop_rule_caps_the_skip_rate`,
`benchmark/results/untraced-paths.md` (missed 1 of 2 failures without the marker,
0 of 2 with it).

*Consequences.* The stop rule makes the tool *never* report "0 tests run" for an
unchanged tree; it selects the highest-risk test instead.

### ADR-7 — Defensive plugin, isolated state, no third-party dependencies

*Options.* (a) rely on the plug-in contract and let errors propagate; (b) wrap
every hook in a guard that degrades to a plain full run and records a warning.

*Decision.* (b), plus "no third-party runtime dependency".

*Rationale.* A test-selection tool that breaks the build is worse than no tool.
Every observable side effect is confined to `.risktest/`; the only required
interpreter feature is `sys.monitoring`, and its absence is reported.

*Evidence.* `RiskTestController.pytest_collection_modifyitems` and
`pytest_sessionfinish` capture exceptions; `tests/test_plugin_integration.py`
asserts the plugin is inert without `--risktest`; the package declares `dependencies = []`.

*Consequences.* Failures inside the tool are silent by design; the run report
carries a `warnings` array so the degradation is still visible to the reviewer.

