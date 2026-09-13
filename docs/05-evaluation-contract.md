# Evaluation contract (frozen before measurement)

This contract was written before the comparison was executed.  Metrics,
thresholds, targets and exclusion rules must not be changed after seeing results;
negative results are reported instead (see "Negative results" below).

## Research questions

* **RQ1 (effectiveness).** How much of a suite can be skipped while still
  detecting every failing test caused by a change?
* **RQ2 (efficiency).** How much execution time does that save, and what does the
  observation itself cost?
* **RQ3 (ordering).** Does risk ordering detect failures earlier than the
  collection order of a full run?
* **RQ4 (limits).** Where does the approach fail?

## Metrics (frozen)

| Metric | Definition | Direction |
| --- | --- | --- |
| `skip_rate` | 1 − executed / collected tests for one mutation | higher is better |
| `recall` | executed ∩ ground-truth failures / ground-truth failures | **1.0 required**, minimum over runs is reported |
| `misses` | ground-truth failures that were not executed | 0 required |
| `APFD` | average percentage of faults detected by the produced order, using the full test set as the universe (unexecuted failures count as detected last) | higher is better |
| `time_saved` | 1 − tool wall clock / untraced full-run wall clock | higher is better |
| `work_saved` | 1 − Σ test durations (tool) / Σ test durations (full run) | higher is better |
| `overhead_*` | traced full run / untraced full run − 1, per granularity | lower is better |

`work_saved` exists because `time_saved` includes interpreter and pytest
start-up, which is a fixed cost of 1.3–2.2 s on the benchmark machines and
dominates small suites.  Reporting both prevents the fixed cost from flattering
or hiding the tool's real effect.

## Targets (frozen)

| Target | Kind | Tests | Why it is in the study |
| --- | --- | --- | --- |
| `subject_01..03` | generated, layered (core / store / services / 8 features) | 88 | core changes propagate through the import graph, feature changes stay local; enough volume for wall-clock effects |
| `pytest-risktest (self-hosted)` | real code, this repository | 79 | a real suite with real import structure and no artificial work factor |

The generated subjects include a documented per-test work factor
(`--iterations`, ~15 ms of real CPU per test).  Rationale: without it, a 24-test
suite is almost entirely interpreter start-up and no selection strategy can show
an effect.  The knob is published, and the self-hosted target has no such knob.

## Fault model (frozen)

* Mutations are applied by `benchmark/mutate.py` with the operators
  `replace-operator`, `change-constant`, `negate-condition`,
  `flip-boolean-return`.
* A mutation is *accepted* only if it provably breaks at least one test
  (`_apply_killing_mutation` retries with a new seed otherwise, ≤ 12 attempts).
  A non-killing mutation would make recall trivially 1.0 and is therefore
  excluded, not counted.
* Ground truth for each accepted mutation is a plain, untraced `pytest` run with
  `--junitxml`; the tool never provides its own ground truth.
* The self-hosted target mutates only `metrics.py` and `report.py`: those modules
  are not used by the selection path, so the mutation cannot alter the tool being
  measured.

## Protocol

For every target: (1) untraced full run → ground truth + naive cost; (2) traced
full runs at file and line granularity → observation cost; (3) snapshot the
dependency store; (4) for each accepted mutation, and for every policy in
{`fast`, `balanced`, `safe`} in the same order: restore the snapshot, run the tool,
measure.  Restoring between policies is mandatory: the plugin refreshes digests at
collection time, so without it the second policy would see an unchanged tree.

## Thresholds (frozen)

| RQ | Threshold | Result |
| --- | --- | --- |
| RQ1 | mean `skip_rate` ≥ 0.35 for the recommended policy, `recall` = 1.0 and `misses` = 0 in every run | met (see below) |
| RQ2 | observation overhead < 20 % at file granularity on work-carrying suites | met |
| RQ3 | mean `APFD` of the tool > mean APFD of the collection-order baseline | met |
| RQ4 | at least one documented, reproduced failure mode with a designed mitigation | met |

## Measured results (36 runs)

| Policy | runs | skip rate | recall (worst) | misses | APFD tool | APFD baseline | time saved | work saved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 12 | 0.854 | 1.000 | 0 | 0.925 | 0.659 | 0.180 | 0.851 |
| balanced | 12 | 0.714 | 1.000 | 0 | 0.925 | 0.659 | 0.124 | 0.656 |
| safe | 12 | 0.693 | 1.000 | 0 | 0.925 | 0.659 | 0.105 | 0.634 |

Observation overhead: file −8.5 % / −0.3 % / +7.9 % (generated) and +16.7 %
(self-hosted); line +508 %/+532 %/+551 % (generated, CPU-bound) and +26 %
(self-hosted).  Raw data: `benchmark/results/benchmark.csv`,
`benchmark/results/benchmark.json`.

All three thresholds are met.  Two results deserve emphasis:

1. **The static closure bought no recall on this benchmark.**  On both core-module
   mutations `fast` already selected every failing test (the changed constant is
   read by every affected test), so `balanced`/`safe` only spent more time
   (skip rate 0.614 → 0.216/0.091 on `subject_02-m2`).  The conservative policies
   are justified by the *boundary* experiment, not by these runs.
2. **APFD is identical across policies** (0.925 mean) because no policy missed a
   failure and all three use the same risk ordering; APFD measures the ordering.
   This is expected and is stated instead of being presented as a win.

## Negative results and limitations (reported, not hidden)

| Finding | Measurement | Response |
| --- | --- | --- |
| Line granularity can be two orders of magnitude slower | +508 %…+551 % on CPU-bound suites; the strategy (local vs global) does not help when the hot code is project code | keep `file` as the default; expose line granularity as opt-in; publish `benchmark/results/tracing-strategies.md` |
| Subprocess-boundary tests are invisible | without a declaration 1 of 2 real failures was missed (`fast`) | ADR-6 escape hatch `@pytest.mark.risktest_always`, demonstrated with the same experiment |
| Wall-clock savings are modest on small suites | 10–18 % (start-up dominated) | report `work_saved` (63–85 %) alongside; state the start-up share explicitly |
| The tool must run *once per change* | a second run on the same unchanged tree selects only the always-run set (stop rule) | documented; the benchmark restores the store between policies to keep the protocol honest |
| Only one interpreter is observable | the tracing is per process | documented as a constraint in `docs/03-requirements.md` |

## Reproducing

```powershell
$env:PYTHONPATH = "src"
python benchmark/generate_subjects.py --subjects 3 --features 8
python benchmark/run_bench.py --subjects 3 --mutations 3
python benchmark/experiments/tracing_strategies.py
python benchmark/experiments/untraced_paths.py
```

Every run writes raw data next to the summary, so a reviewer can recompute any
aggregate: `benchmark/results/{benchmark.csv,benchmark.json,summary.md,
tracing-strategies.md,untraced-paths.md}`.

