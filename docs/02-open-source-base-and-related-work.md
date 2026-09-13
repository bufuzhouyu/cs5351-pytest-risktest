# Open-source base selection and related work

## Candidate bases

| Candidate (open source) | Plug-in surface | Research backing | Evaluation signal available offline | Verdict |
| --- | --- | --- | --- | --- |
| **pytest** (pytest-dev/pytest) | documented `pytest11` entry point, ~50 hooks (`pytest_collection_modifyitems`, `pytest_runtest_*`) | test selection/prioritisation, flakiness detection | per-test outcomes and durations, JUnit XML, deterministic subjects | **selected** |
| ESLint (eslint/eslint) | rich rule/plugin API | code-smell research | needs a labelled smell corpus | possible, weaker data story |
| Gradle/Maven test plug-ins | build-level hooks | build avoidance, TIA | heavyweight, JVM toolchain not available in the project environment | rejected (environment) |
| SonarQube / PMD / Checkstyle | analysis rules | smell/debt research | needs ground-truth label sets | rejected (data availability) |
| logparser-family log analysis tools | library API | log parsing (Drain, Spell) | needs Loghub datasets (no network at evaluation time) | rejected (data availability) |

`pytest` wins on three practical criteria: the plug-in boundary is stable and
documented, the *ground truth* of a test run (pass/fail per test) is available
without extra labelling, and the whole evaluation can run offline and be
reproduced by a reviewer with a single command.

## Related work and how this project differs

| Work / tool | Idea | What we reuse | What we do differently |
| --- | --- | --- | --- |
| Test Impact Analysis as used by build systems (Bazel, Gradle, Microsoft/Google internal TIA) | map a change to the tests that executed the changed code | observed-execution dependency model | we fuse the observed model with a *static import closure* and expose the trade-off as named, auditable policies instead of one fixed rule |
| Predictive Test Selection (Meta, 2019→; Google's TAP) | rank tests by predicted failure probability, run a subset under a confidence target | prioritisation by features (history, recency, impact) | no ML model: features are local, explainable and stored in one SQLite file; the tool reports *why* every test was selected |
| `pytest-testmon` | coverage-based selection for pytest | the idea of persisting per-test dependencies and re-running affected tests | we add prioritisation, flakiness triage, policy/stop-rule controls, and measured observation overhead (PEP 669 instead of a full tracer) |
| `pytest-xdist`, `pytest-randomly` | parallelism / order randomisation | seeded order perturbation | we use order perturbation as a *flakiness oracle* (`risktest flaky-check`) and for differential flakiness |
| iDFlakies / FlakyFlix (flakiness detection) | re-run tests in perturbed orders to expose order dependence | order-perturbation idea | full re-runs are too expensive for a *time-saving* tool, so we combine one perturbed rerun with a cheap differential signal: same dependency fingerprint, different outcome |
| "Predictive Test Selection" (ICSE'20) and "Reducing Test Cost" style studies | report recall/AFPD-type trade-offs | APFD, recall, skip-rate metrics | the study protocol is frozen before measurement (`docs/05-evaluation-contract.md`), and negative results are reported (line-granularity cost, subprocess blind spot) |
| SWEBOK v4.0, DORA 2025, NIST SP 800-218, NIST AI RMF 1.0 | software engineering body of knowledge; evidence on how AI-assisted development amplifies the surrounding delivery system; secure development and AI risk frameworks | process framing, risk register, evidence discipline | the project applies them as review gates: every AI-assisted change carries tests, rationale and a reviewable patch (`docs/07-coding-agent-contract.md`) |

## The original contribution (what is new here)

1. **Evidence fusion with an explicit safety budget.**  Observed execution,
   static closure, run history and flakiness are combined into one plan, with a
   stop rule that bounds the maximum skip rate and an always-run set that no
   policy may override.
2. **Deferred local line instrumentation on PEP 669.**  Instead of enabling line
   events for the whole interpreter, the tool enables them lazily per code object
   from the `PY_START` callback and disables the now-redundant entry event; code
   outside the project never pays for line events.  Measured effect
   (`benchmark/results/tracing-strategies.md`): on a library-dominated workload
   overhead drops from +97 % (global) to −2 % (local); on a hot-loop workload both
   strategies cost ~60×, which is why *file* granularity is the default.
3. **Explainable prioritisation without a model.**  The risk score is a documented
   weighted sum of observable state, so a reviewer can reproduce any ordering from
   the SQLite store and the run report.
4. **Boundary honesty.**  The project measures where the approach fails
   (subprocess-boundary tests) and turns it into a documented, tested escape hatch
   (`@pytest.mark.risktest_always`) instead of an implicit assumption.

