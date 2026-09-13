# Bounded problem statement

## User, workflow and trigger

* **User** — a developer (or an automated CI pipeline) working on a Python
  project whose test suite is large or slow.
* **Workflow** — change source code, run the test suite, fix what broke, push.
* **Trigger** — a commit or a pull request: a small, localised edit must be
  verified before it reaches the main branch.

## The current failure

The default answer to "did my change break anything?" is to run everything.

* On the generated benchmark subjects the full suite takes 1.4–1.9 s of which
  only a fraction is related to the edit; on this project's own suite the
  untraced baseline is ~1.9 s and the *work* in the tests is a similar order of
  magnitude.  On real projects the ratio is far worse — this is the pain the
  Coursera-style "run everything" loop creates: **feedback latency grows with
  suite size, not with the change**.
* Naive attempts to skip tests are worse than running everything: an unsafe
  selection silently hides a regression, which is a *product quality* failure,
  not a performance one.

Observable baseline evidence (measured, reproducible):

| Measurement | Value | Source |
| --- | --- | --- |
| full-suite wall clock, four targets | 1.36–1.88 s untraced | `benchmark/results/summary.md` |
| tests that actually fail after a verified mutation | 1–3 of 88 (or 1 of 79) | `benchmark/results/benchmark.csv` |
| share of the suite a change really needs | 9–31 % | same file |
| observation cost of the tool on a pristine tree | −8.5 %…+16.7 % (file granularity) | same file |
| order a full run detects failures in | APFD 0.659 (collection order) | same file |

## One measurable outcome

**Execute at most 35 % of a test suite on average for a single verified mutation,
detect every failing test (recall = 1.0), and raise the fault-detection order
(APFD) above the collection-order baseline.**

The contract, thresholds and exclusion rules are frozen in
`docs/05-evaluation-contract.md` before any comparison is run.

## Non-goals

* Not a test *generator* and not a replacement for writing tests.
* Not a build system, CI runner, or remote cache.
* Not a mutation-testing framework: mutation is used only as a *controlled fault
  source* for the evaluation.
* No coverage of non-Python projects, and no guarantee for code executed outside
  the instrumented interpreter (subprocess-boundary tests) — the escape hatch for
  that case is documented and tested instead
  (`benchmark/results/untraced-paths.md`).
* No machine-learning model: every decision must be explainable in the run report,
  because an unexplainable skip decision cannot be reviewed.

## Why an open-source base is the right choice here

The course recommends starting from an operable open-source project or a project
that supports plug-ins, ideally related to a research paper.  `pytest` is exactly
that: a mature open-source project with a documented plug-in API, and the problem
we attack (test impact analysis, predictive test selection, flaky test detection)
has an established literature.  The selection and comparison of candidate bases
is documented in `docs/02-open-source-base-and-related-work.md`.

