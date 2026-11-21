# Sprint 3 (weeks 10–13) — automated testing, debugging support, wrap-up

Sprint 2 activities plus automated testing, debugging and maintenance support.

| Story | Points | Owner | Planned outcome | Status |
| --- | --- | --- | --- | --- |
| End-to-end acceptance suite in CI (subprocess plugin runs) | 5 | 代佳乐 (M2) | the ten integration tests run on every push | tests written and wired to CI |
| Boundary experiment (untraced paths) + escape-hatch documentation | 5 | 代佳乐 (M2) | the limitation is measured, not assumed | done |
| Maintenance: `risktest clean/status`, store recovery, troubleshooting guide | 3 | 肖宇 (M3) | a new user can recover a broken state | CLI done; guide to write |
| Evaluation re-run and report §7 | 8 | 张力元 (M4) | frozen protocol, all numbers regenerated | first run done; re-run after sprint 2 landings |
| Offline presentation + live demo | 5 | 庄志洋 (M5) | 7-minute talk, live end-to-end demo, backup screenshots | deck and script ready; rehearsal needed |
| Report assembly in the IEEE TSE template | 8 | 周浩然 (M6) | section owners, one editor | draft ready |
| Process self-reflection | 3 | ALL | what the team would change next time | to write |

**Demo plan (frozen, no future features)**

1. `pytest -p pytest_risktest.plugin --risktest --risktest-policy=off` on a fresh
   clone (warm-up).
2. Edit one source file, run `risktest impact` (dry run, shows the plan).
3. Run `pytest --risktest --risktest-policy=safe` and show the report.
4. Break a source file, re-run: the failure is still reported (safety).
5. Show the benchmark figure and the untraced-path experiment.

