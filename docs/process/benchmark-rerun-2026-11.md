# Benchmark re-run (November 2026)

## Environment and commands

- Date: 2026-11-22
- Host: Windows 10 x64 (build 19045), Intel Core i7-11800H @ 2.30 GHz
- Python: CPython 3.14.6 (Anaconda), pytest 9.0.3
- Repository baseline: `f0172a4eaafcf65f238f07e7d5367e065214cffc`
- Main run: file granularity, eight features and 45,000 work iterations per generated target

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONUTF8 = "1"
python benchmark/generate_subjects.py --subjects 3 --features 8 --seed 20260102
python benchmark/run_bench.py --subjects 3 --mutations 4 --seed 20260102
python benchmark/experiments/tracing_strategies.py
python benchmark/experiments/untraced_paths.py
python -m pytest tests -q
```

The runner adds the self-hosted target automatically. The frozen study targets
are `subject_01`, `subject_02`, `subject_03`, and `pytest-risktest (self-hosted)`.
Each target had four distinct mutations that caused at least one failure in a
plain full pytest run. The three policies ran on every mutation, for 48 runs.

## Results

| Policy | Runs | Mean skip rate | Worst recall | Missed failures | Mean APFD (tool / baseline) | Mean wall-clock saved | Mean work saved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fast | 16 | 85.24% | 1.000 | 0 | 0.925 / 0.521 | 25.15% | 85.29% |
| balanced | 16 | 74.63% | 1.000 | 0 | 0.925 / 0.521 | 19.66% | 69.44% |
| safe | 16 | 73.06% | 1.000 | 0 | 0.925 / 0.521 | 18.54% | 67.48% |

- Main run output: `subject_01`, `subject_02`, and `subject_03` each recorded
  `12 runs, 88 tests`. The self-hosted target recorded `12 runs, 103 tests`.
- The tracing microbenchmark completed eight workload/strategy combinations.
  On its hot loop, local and global line tracing both added over 6,000% overhead.
- The subprocess experiment reproduced one missed failure out of two without
  `risktest_always`. With both tests marked, it found both failures.
- Repository test suite: `121 passed`.

[Summary](../../benchmark/results/summary.md) ·
[CSV](../../benchmark/results/benchmark.csv) ·
[JSON](../../benchmark/results/benchmark.json) ·
[Tracing experiment](../../benchmark/results/tracing-strategies.md) ·
[Subprocess experiment](../../benchmark/results/untraced-paths.md) ·
[Figures](../report/figures/)

## Interpretation

The prior 36-run baseline also had 100% worst-case recall and no missed
failures. Fast's skip rate was similar (85.4% then, 85.2% now), while balanced
and safe rose from 71.4% and 69.3% to 74.6% and 73.1%. One self-hosted change
to `report.py` illustrates the trade-off: balanced and safe selected 94 tests through transitive dependencies and ran all 103 tests. Fast ran ten tests and detected
the same three failures. All three strategies matched the prior tool APFD of
0.925. The current collection-order baseline was lower (0.521 versus 0.659).

File tracing added 6.47–12.87% on the three generated suites, below the 20%
threshold for work-carrying suites. Self-hosted overhead reached 28.28%.
The generated suites' line overhead ranged from 1,158.09% to 1,293.10%.
The seed, self-hosted test count (79 previously, 103 now), Python environment,
and timing conditions limit comparisons across runs. The subprocess result
also limits the scope of the main run's zero-miss result.

## Problems and protocol decisions

The initial run with the default seed `20260101` completed 48 policy runs
with zero misses, but it repeated one self-hosted mutation. A preflight
compared file, line, operator and before/after text for the four accepted
mutations per target. The next seed, `20260102`, was the first checked seed
with four distinct mutations on all targets. The results above use that
seed throughout. The published harness and evaluation contract were used
as-is.
