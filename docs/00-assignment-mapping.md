# Course requirements → repository artefacts

This document maps every requirement of `week1-cs5351-project.pdf` onto concrete
artefacts in this repository, so that the mapping can be audited without reading
the whole repository.

## Deliverables and milestones

| Slide | Requirement | Where it is satisfied | Status |
| --- | --- | --- | --- |
| 2 | A *software engineering tool* for developers, not an end-user app | `pytest-risktest` runs as a pytest plugin inside the developer's own workflow | done |
| 3 | Size: single-person FYP for a team of six | ~6 200 lines of Python across source, tests and benchmark (2 212 in the tool itself); 3 sprints of work planned | done for sprint-1 scope |
| 4 | Team of 5–8, at least two non-functional requirements, each addressed by an architectural design option with rationale | NFR-1 performance, NFR-2 reliability, NFR-3 scalability → `docs/04-architecture.md` ADR-1…ADR-7, each with measurements | done |
| 4 | Agile with at least three cycles, weekly standing meeting, burndown chart | `docs/process/sprint-1..3.md`, `docs/process/burndown.csv`, `docs/report/figures/burndown.svg` | sprint plans + chart ready; weekly actuals to be maintained by the team |
| 5 | Repository captures weekly activities as evidence | `.github/` templates, one issue per story, `CHANGELOG.md`, sprint evidence tables, CI workflow | templates and CI ready; team adds weekly entries |
| 6 | Presentation + demo video (5 %) | `docs/report/presentation-outline.md` | outline ready; slides/video are team work |
| 6 | Final report (20 %) ~10 000 words, IEEE TSE structure | `docs/report/report-draft.md` (+ figures in `docs/report/figures/`) | technical sections drafted with real data |
| 8 | Tool must help developers perform development tasks, not operate a deployed service | it selects/prioritises/runs tests and reports flakiness — a pre-deployment development activity | done |
| 10 | Start from an operable open-source project or a project that allows plug-in development; best if related to a research paper | base = **pytest** (plugin API), problem from the test-selection / flakiness literature → `docs/02-open-source-base-and-related-work.md` | done |
| 10 | Implement original/improved algorithms for a specific development problem | adaptive multi-signal selection + risk ordering + differential flakiness + deferred local line instrumentation (PEP 669) | done |
| 11–12 | Improvement on existing tasks / extension / applicability change | improves test impact analysis (precision *and* safety), extends it with prioritisation and flakiness triage | done |
| 14 | Relative contribution table | template at the end of `docs/report/report-draft.md` | team must fill in hours |
| 15 | Milestone 0: team list, team name, project name | `<team name>` / `<project name>` placeholders in `README.md` | team must fill in |
| 16 | Source code on GitHub | this repository (git-initialised, one commit per logical change) | ready to push |
| 17 | Report in IEEE TSE format | Markdown draft with the required section structure and figure placeholders | team must transfer to the Word/LaTeX template |
| 18–20 | Report content: title, abstract, introduction, related work, preliminaries, solution, software process + burndown, evaluation, conclusion, bios, relative contribution | `docs/report/report-draft.md` (sections 1–8 drafted); bios/self-reflection/contribution are personal and left to each student | partially — see "must be completed" below |
| 22 | Project idea filter: serve a developer workflow, pain observable before the tool exists, demonstrable by week 13 | `docs/01-problem-statement.md` §"Observable pain" + benchmark baseline numbers | done |
| 23 | Bounded problem statement: user, workflow, trigger, current failure, one measurable outcome, explicit non-goals | `docs/01-problem-statement.md` | done |
| 24 | Baseline → change → measure, and isolate the changed behaviour | `benchmark/run_bench.py` measures untraced baseline, traced baseline and the tool on verified mutations | done |
| 25 | Trace requirement to result: issue → PR → tests → closing syntax | `docs/08-trace-requirement-to-result.md` + issue/PR templates | done |
| 26 | Keep weekly repository evidence | `docs/process/weekly-evidence.md`, sprint documents, CHANGELOG | structure ready |
| 27 | Coding-agent use contract: bounded tasks, tests + rationale + reviewable PR, humans own the output | `docs/07-coding-agent-contract.md` | done |
| 28 | Risk register and stop rules | `docs/06-risk-register.md` (risk, trigger, likelihood, impact, owner, mitigation, decision date; explicit stop rules) | done |
| 29 | Freeze the evaluation contract before comparison; make evidence visible at review; report negative results | `docs/05-evaluation-contract.md` (frozen metrics and thresholds) + `benchmark/results/` incl. the negative boundary experiment | done |
| 30 | Core references (SWEBOK, DORA, NIST) and practical resources (GitHub Copilot agents, Spec Kit, status checks, value stream management) | `docs/report/report-draft.md` §References and `docs/07-coding-agent-contract.md` | done |

## What is already complete

* a working tool (`src/pytest_risktest`, 2 212 lines) with an entry point, CLI and pytest plugin;
* 96 automated tests, including ten end-to-end tests that drive the plugin in
  real subprocesses and assert the safety properties;
* a reproducible evaluation harness with four targets, verified mutations, three
  policies, 36 measured runs, and three dedicated experiments (tracing
  strategies, boundary/untraced paths, self-hosted target);
* the engineering documentation: problem statement, requirements, architecture
  decisions with measurements, evaluation contract, risk register, coding-agent
  contract, traceability matrix, sprint plans and the report draft.

## What the team must still complete

These items are deliberately *not* fabricated here, because they require the
team's own decisions, hours or personal reflection:

1. **Names and identifiers** — team name, project name, member list with student
   IDs, and the GitHub repository URL (`README.md`, `docs/report/report-draft.md`).
2. **Weekly evidence and burndown actuals** — weeks 2–13 are still to be lived:
   fill `docs/process/weekly-evidence.md`, `docs/process/burndown.csv` and the
   sprint review logs each week (issue → commit → test evidence).
3. **Relative contribution and student bios** — `docs/report/report-draft.md`
   §9–§10 (hours/story points per member, pro-rating calculation, per-student
   self-reflection, declaration).
4. **Presentation and demo video** — 7 minutes; outline provided in
   `docs/report/presentation-outline.md`, slides and recording are team work.
5. **Report formatting** — move the Markdown draft into the IEEE TSE Word/LaTeX
   template, expand the related work with the team's own reading notes, and add
   the figures from `docs/report/figures/`.
6. **Decisions to confirm** — the team should review ADR-1…ADR-7
   (`docs/04-architecture.md`), accept or override them, and record the decision
   date and owner in the sprint log.  An accepted ADR the team did not discuss
   is not an engineering decision.
