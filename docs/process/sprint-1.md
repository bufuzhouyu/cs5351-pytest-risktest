# Sprint 1 (weeks 2–5) — walking skeleton, traces, selection

**Goal.** A plugin that observes test→file dependencies on a real pytest run and
uses them to run only the affected tests, with the safety net in place.

**Sprint backlog (story points)**

| Story | Points | Owner | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| US-1 trace tests to files | 8 | R1 | dependency edges exist per executed test | done |
| US-2 select only affected tests | 8 | R1 | changed module → only its tests run | done |
| US-3 safety net for unknown/failing/flaky tests | 5 | R2 | always-run set proven by unit tests | done |
| US-8 zero-dependency operation + CLI | 5 | R2 | `risktest status/impact/report/clean` work | done |
| NFR-1 PEP 669 monitor | 8 | R3 | overhead measured, not asserted | done |
| NFR-3 store design (SQLite, pruning, digest cache) | 5 | R3 | bounded state, change detection without git | done |
| Risk register, evaluation contract, ADRs | 5 | TL | documents reviewed and dated | done |
| Weekly evidence + issue/PR templates + CI | 3 | ALL | templates and workflow in place | done |

Total 47 points, all complete in the repository state of 2026-09-14.

**Review outcomes**

* Decision: file-level dependencies are the product default (ADR-3) after
  measuring line-level cost.
* Decision: selection must never be able to hide a failure (ADR-5, ADR-6).
* Risk found: the first benchmark design produced mutations that killed no test
  and let consecutive policy runs share state (R-7).  Fixed by a kill check and a
  store snapshot/restore, and recorded in the risk register rather than deleted.
* Owner names (`R1`, `R2`, `R3`, `TL`) are placeholders to be replaced with the
  team's real member names at the first review.

**Evidence**

* repository import with per-module commits
* tests: 95 passing (`pytest tests -q`)
* benchmark: `benchmark/results/summary.md` (36 runs)

