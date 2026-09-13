# Benchmark and experiments

Everything in this directory is *evaluation* infrastructure: it produces the
evidence quoted in `docs/05-evaluation-contract.md` and in the report draft.  It
is not required to use the tool.

## Layout

| Path | Purpose |
| --- | --- |
| `generate_subjects.py` | generates layered subjects from a seed (core / store / services / features + one test module per unit) |
| `subjects/` | the generated subjects, committed so a reviewer can inspect and re-run them |
| `mutate.py` | four auditable mutation operators and the revert logic |
| `run_bench.py` | the harness: untraced baseline, traced baselines, verified mutations, three policies, four targets |
| `results/` | raw CSV/JSON plus the generated summaries and figures |
| `experiments/tracing_strategies.py` | ADR-2 design option: global vs deferred-local line instrumentation |
| `experiments/untraced_paths.py` | RQ4: what dynamic tracing cannot see and the designed escape hatch |

## Why the subjects carry a "work factor"

`generate_subjects.py --iterations 45000` gives every generated test ~15 ms of
real CPU work.  Without it a 24-test suite is almost entirely interpreter and
pytest start-up (≈1.5 s fixed), so no selection strategy can show a wall-clock
effect and `time_saved` would measure noise.  The knob is published, and the
harness reports `work_saved` (test execution time only) next to `time_saved` so
the fixed cost can never flatter the tool.  The self-hosted target (this project's
own unit tests) has no such knob.

## Reproducing

```powershell
$env:PYTHONPATH = "src"

python benchmark/generate_subjects.py --subjects 3 --features 8
python benchmark/run_bench.py --subjects 3 --mutations 3 --granularity file

python benchmark/experiments/tracing_strategies.py --iterations 150000 --library-iterations 400
python benchmark/experiments/untraced_paths.py
```

`run_bench.py` regenerates the subjects at every start (deterministic from
`--seed`), applies a mutation, verifies that the mutation kills at least one test,
measures the tool, reverts the mutation, and restores the dependency store from a
snapshot before the next policy run.  A run that skips one of these steps would
produce invalid evidence; each of them was added after observing the failure in
practice (see R-7 in `docs/06-risk-register.md`).

The results committed in `results/` were produced with this protocol.  The
`__pycache__` clearing described below was added afterwards (after the same effect
flaked one integration test); it removes a potential source of *rejected* mutations
and therefore does not invalidate the committed measurements, which all passed the
kill check.

## Reading the results

* `results/summary.md` — aggregated per policy, per target kind, plus every mutation.
* `results/benchmark.csv` — one row per (target, mutation, policy).
* `results/tracing-strategies.md` — observation cost of each instrumentation strategy.
* `results/untraced-paths.md` — the measured blind spot and its mitigation.
* `docs/report/figures/*.svg` — figures generated from the same data.

## Known limitations of the benchmark

* Small suites: 79–88 tests.  Wall-clock savings are diluted by a fixed start-up
  cost of 1.3–2.2 s; `work_saved` is the metric that isolates the tool's effect.
* Synthetic fault model: four operators, one fault at a time.  Real regressions
  may be multi-line and semantic; the operators are documented so the threat to
  validity is explicit.
* The self-hosted target mutates only `metrics.py` and `report.py`, the two
  modules that the selection path does not use, so the mutation cannot change the
  tool being measured.
* Timing on a shared Windows laptop: the harness reports one measurement per
  configuration and the summaries therefore include noise (visible as negative
  overhead values); conclusions use only effects that are larger than that noise.
* Stale bytecode: CPython validates a cached `.pyc` using the source file's size
  and its mtime rounded to seconds.  A same-length mutation applied within the same
  second as the previous run would execute the old bytecode and look harmless, so
  `mutate.apply_mutation`/`revert` clear `__pycache__` and the harness verifies that
  every accepted mutation really breaks a test.
