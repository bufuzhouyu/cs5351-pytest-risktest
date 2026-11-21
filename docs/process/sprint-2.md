# Sprint 2 (weeks 6–9) — code quality, prioritisation, flakiness

Sprint 1 activities plus code quality.  The table is the team's backlog for the
sprint: "planned" is what the team agreed at planning time, and the status column
is updated during the sprint reviews.

| Story | Points | Owner | Planned outcome | Status |
| --- | --- | --- | --- | --- |
| US-6 risk ordering with APFD evidence | 5 | 赵尊 (M1) | ordering beats collection order on the frozen targets | metric implemented; re-run in sprint 3 |
| US-7 differential flakiness + `flaky-check` | 8 | 代佳乐 (M2) | order-dependent tests flagged and reproducible | implemented |
| Line-granularity experiment and ADR-2 update | 5 | 赵尊 (M1) | local vs global instrumentation measured | done |
| Code quality: type hints, docstrings, dead code removal | 3 | ALL | review checklist applied to every module | to be scheduled |
| Refactor: policies as data, stop rules configurable | 3 | 赵尊 (M1) | adding a policy needs no engine change | done |
| Extend the benchmark to the self-hosted target | 5 | 张力元 (M4) | a real suite in the study | done |
| Related-work reading notes (TIA, predictive selection, flakiness) | 5 | 肖宇 (M3) | report §2 material | draft in `docs/02-...md`; team expands |

**Planned sprint review questions**

1. Does prioritisation actually raise APFD on every target, or only on average?
2. Can the flakiness signal produce a false positive (a flaky flag on a genuinely
   deterministic test)?  What is the cost of one perturbed rerun?
3. Is the remaining code small enough for the whole team to read?

