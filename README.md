# pytest-risktest

**Risk-aware test selection, prioritisation and flakiness triage for pytest.**

`pytest-risktest` is a software engineering tool for development teams: it observes
which project files each test really exercises, and then uses that evidence to run
*only the tests a change can affect*, in *risk order*, while refusing to hide a
failure behind its own skip decisions.

This repository is the CS5351 Software Engineering course project (team
`<team name>`, project `<project name>`).  See
[docs/00-assignment-mapping.md](docs/00-assignment-mapping.md) for the mapping
between the course requirements and the artefacts in this repository.

## What it does

| Capability | Detail |
| --- | --- |
| Test selection (TIA) | Fuses *observed* per-test dependencies (PEP 669 monitoring) with the *static* import closure, bounded by an auditable policy (`fast`, `balanced`, `safe`). |
| Prioritisation | Orders the selected tests by risk (recent failures, known flakiness, how much of the changed code the test exercises) to raise APFD. |
| Flakiness triage | Differential flakiness (same dependency fingerprint, different outcome) plus order-perturbation reruns (`risktest flaky-check`). |
| Safety guard rails | Stop rule on the maximum skip rate, always-run set for unseen/failing/flaky tests, `@pytest.mark.risktest_always` escape hatch for process-boundary tests. |
| Evidence | JSON/Markdown/HTML run reports, SQLite dependency store, benchmark harness with a frozen metric contract. |

## Install and run

The tool has **no third-party runtime dependencies** (Python 3.12+ is required for
`sys.monitoring`).

```powershell
# from the repository root, without installing anything
$env:PYTHONPATH = "src"

# 1) warm-up run: record dependency traces, execute everything
python -m pytest tests -p pytest_risktest.plugin --risktest --risktest-policy=off

# 2) after a change: run only the affected tests, in risk order
python -m pytest tests -p pytest_risktest.plugin --risktest --risktest-policy=safe
```

Installed as a package the plugin is loaded automatically:

```powershell
pip install -e .
pytest --risktest --risktest-policy=safe
```

### Command line

```powershell
risktest status                     # what the tool knows about this repository
risktest impact --policy safe       # dry run: which tests would a change trigger?
risktest flaky-check -- pytest -q   # order-perturbation reruns, flags flaky tests
risktest report --report .risktest/last-run.json
risktest clean --yes                # delete local state
```

### Key options

| Option | Meaning |
| --- | --- |
| `--risktest-policy={off,fast,balanced,safe}` | how much of the impact closure is selected (`off` = trace only, `safe` = recommended for CI) |
| `--risktest-granularity={file,line}` | dependency granularity; `file` is the measured default |
| `--risktest-line-strategy={local,global}` | per-code-object (default) or interpreter-wide line events |
| `--risktest-order={risk,original,shuffle}` | ordering of the selected tests |
| `--risktest-changed={auto,hash,git,none}` | change detection (works without git) |
| `--risktest-max-deselect=90` | stop rule: never deselect more than this share of the suite |
| `--risktest-trace-only` | record traces but run everything |

## Measured results

All numbers come from `benchmark/run_bench.py`, which injects *verified* mutations
(mutations that provably break at least one test) into four targets: three
generated layered projects and this project itself (self-hosted).  Full detail:
[benchmark/results/summary.md](benchmark/results/summary.md).

| Policy | runs | skip rate | recall (worst) | missed failures | APFD tool | APFD baseline | work saved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 12 | 0.854 | 1.000 | 0 | 0.925 | 0.659 | 0.851 |
| balanced | 12 | 0.714 | 1.000 | 0 | 0.925 | 0.659 | 0.656 |
| safe | 12 | 0.693 | 1.000 | 0 | 0.925 | 0.659 | 0.634 |

* *work saved* excludes interpreter start-up and uses per-test durations only.
* observation overhead: file granularity ≈ 0–17 %, line granularity 26 % on this
  project's suite and > 500 % on CPU-bound generated suites
  ([benchmark/results/tracing-strategies.md](benchmark/results/tracing-strategies.md)).
* a boundary experiment shows the case the approach cannot see and the designed
  mitigation: [benchmark/results/untraced-paths.md](benchmark/results/untraced-paths.md).

## Repository layout

```
src/pytest_risktest/   plugin, monitor (PEP 669), graph, store, selector, flaky, metrics, report, CLI
tests/                 99 tests: unit tests plus end-to-end plugin tests in subprocesses
benchmark/             subject generator, mutation operators, harness, experiments, results
scripts/               dev helper, burndown chart, store inspector, dependency-map exporter
docs/                  assignment mapping, problem statement, requirements, architecture, process, report draft
.github/               issue and pull-request templates, CI workflow
```

## Documentation

| Document | Content |
| --- | --- |
| [docs/00-assignment-mapping.md](docs/00-assignment-mapping.md) | every course requirement → where it is satisfied |
| [docs/01-problem-statement.md](docs/01-problem-statement.md) | bounded problem statement and non-goals |
| [docs/02-open-source-base-and-related-work.md](docs/02-open-source-base-and-related-work.md) | open-source base selection and related work |
| [docs/03-requirements.md](docs/03-requirements.md) | user stories, acceptance criteria, non-functional requirements |
| [docs/04-architecture.md](docs/04-architecture.md) | components and architecture decision records with measurements |
| [docs/05-evaluation-contract.md](docs/05-evaluation-contract.md) | frozen metrics, thresholds and test cases |
| [docs/06-risk-register.md](docs/06-risk-register.md) | risk register and stop rules |
| [docs/07-coding-agent-contract.md](docs/07-coding-agent-contract.md) | how coding agents were used and reviewed |
| [docs/08-trace-requirement-to-result.md](docs/08-trace-requirement-to-result.md) | requirement → code → test → evidence matrix |
| [docs/process/](docs/process/) | sprint plans, weekly evidence, burndown |
| [docs/report/report-draft.md](docs/report/report-draft.md) | final-report draft in the IEEE TSE structure |
| [docs/report/presentation.pptx](docs/report/presentation.pptx) | 10-slide, 7-minute presentation deck |
| [docs/report/narration-script.md](docs/report/narration-script.md) | timed narration script and recording checklist |
| [scripts/demo.ps1](scripts/demo.ps1) | one-command live demo used in the recording |

## Development

```powershell
.\scripts\dev.ps1              # unit + integration tests
.\scripts\dev.ps1 -Benchmark   # reproduce the evaluation
```

## License

MIT, see [LICENSE](LICENSE).
