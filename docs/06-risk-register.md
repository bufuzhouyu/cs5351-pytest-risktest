# Risk register and stop rules

Owners: `R` = developer responsible for the mitigation, `TL` = team leader,
`ALL` = whole team.  "Trigger" is the observable signal that turns a risk into an
action; the decision date is when the team last reviewed it.

## Risks

| ID | Risk | Trigger | Likelihood | Impact | Owner | Mitigation | Decision date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-1 | A change-caused failure is skipped → a red commit looks green | recall < 1.0 in any benchmark run, or a missed failure in CI | medium | **critical** (product quality) | R (selector) | always-run set (unseen/failing/flaky tests); static closure in `balanced`/`safe`; stop rule; `risktest_always` marker; recall is the frozen primary metric | 2026-09-14 |
| R-2 | Observation overhead makes the tool slower than running everything | overhead > 20 % at file granularity | low | high | R (monitor) | PEP 669 instead of a full tracer; per-code-object line instrumentation; digest caching; file granularity default; measured on every benchmark run | 2026-09-14 |
| R-3 | The dependency model goes stale (deselected tests never refresh their traces) | a test is selected only because of the static closure for several consecutive runs | medium | medium | R (store) | always-run set for previously failing/flaky tests; `--risktest-trace-only` warm-up documented; the report shows the reason histogram so staleness is visible | 2026-09-14 |
| R-4 | Code executed outside the instrumented interpreter is invisible (subprocess, another runtime) | a mutation of such code is missed | medium | high | R (docs) + ALL | documented boundary; `risktest_always` marker; boundary experiment in the results directory; US-9 acceptance test | 2026-09-14 |
| R-5 | Tool dependency/compatibility breaks a user's build | no free `sys.monitoring` tool id, Python < 3.12, or an unexpected exception in a hook | medium | **critical** (blocks the user) | R (plugin) | no third-party dependency; defensive try/except in hooks that degrades to a full run; `warnings` array in the report; `--no`-style opt-in flag | 2026-09-14 |
| R-6 | Unbounded state growth on long-lived suites | store size grows run over run | low | medium | R (store) | per-test outcome window of 20, per-run replacement of edges, pruning of vanished tests, WAL SQLite single file; `risktest clean` | 2026-09-14 |
| R-7 | Benchmark flatters the tool (unrealistic subjects, non-killing mutations, shared state between policies) | mutation that kills no test, or a policy run that sees no change | high (already observed twice) | high (invalid evidence) | TL + R (benchmark) | accepted-mutation rule (kill check with retry), untraced ground truth, store snapshot/restore between policies, published work factor, self-hosted target | 2026-09-14 |
| R-8 | Scope creep: "make it a full CI product" | any story that requires a server, database or network | medium | high | TL | frozen non-goals in `docs/01-problem-statement.md`; new ideas go to the backlog, not into the sprint | 2026-09-14 |
| R-9 | Free-riding / uneven contribution | a member's weekly evidence is missing twice in a row | medium | medium | TL | weekly evidence table with owner per story; hours/story points in the contribution table; pro-rating per the course rule | — |
| R-10 | Presentation/video done at the last minute | no demo script by week 10 | medium | high | ALL | outline in `docs/report/presentation-outline.md`; demo path frozen with the acceptance tests | — |
| R-11 | AI-assisted code is merged without review or tests | a change with no linked test or no reviewer | medium | high | ALL | coding-agent contract (`docs/07-coding-agent-contract.md`): bounded task, tests required, human reviewer may reject; CI status check on every PR | 2026-09-14 |

## Stop rules (proceed / no-proceed)

1. **Do not ship a policy that misses a failure.**  If any accepted mutation in
   the frozen benchmark shows `misses > 0` for the recommended policy, the policy
   is not the default until the cause is understood and the contract is updated in
   writing.
2. **Do not exceed the performance budget silently.**  If file-granularity
   overhead exceeds 20 % on the work-carrying suites, switch the default to
   `--risktest-trace-only` + explicit impact queries until the cause is fixed.
3. **Stop and re-scope when the evidence closes the value.**  If the measured
   mean `skip_rate` on the frozen targets falls below 0.35 while recall stays
   1.0 (i.e. selection no longer saves anything), the selection feature is not
   worth its complexity; report that and pivot the remaining sprints to the
   flakiness and reporting features instead of adding scope.
4. **Never change the goalposts after seeing results.**  Metrics, targets,
   thresholds and exclusion rules are frozen in
   `docs/05-evaluation-contract.md`; a change requires a dated note in the sprint
   log and a re-run of the whole protocol.
5. **Escalate a red CI check rather than skipping it.**  The status check is the
   evidence that a requirement's tests actually ran; disabling it is a
   no-proceed condition for a pull request.

