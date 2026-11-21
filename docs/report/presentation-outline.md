# Offline presentation outline (7 minutes)

Format: slides on the projector plus a live terminal demo on the presentation
laptop.  There is no video deliverable for this session.  Rehearse on the actual
room equipment.  Keep a folder of screenshots as a fallback if the projector or
the Python environment fails.

## Before the session

* Open `docs/report/presentation.pptx` in presentation mode and test the projector.
* Open a terminal in the repository root, font size 18 to 20, light background.
* Run `.\scripts\demo.ps1 -NoPause` once to warm the machine, then close it.
* Keep the backup screenshots in `docs/report/figures/` and the Markdown report open.
* Put the phone away, close chat apps and notifications.

## 0:00–0:35 — Background and problem

* The everyday question: "did my change break anything?"  Today the answer is
  "run everything".
* Evidence: a verified change affects 9–31 % of the suite, but 100 % is executed.
* The trap: naive skipping hides regressions.  A false green is a product-quality
  failure.

## 0:35–1:15 — Technical problem and challenges

* Which tests can a change affect, with evidence?
* Challenges: incomplete observation (first run, stale traces, process
  boundaries), observation cost, explainability, and never hiding a failure.
* Related work in one slide: TIA in build systems, predictive test selection,
  coverage-based selection (`pytest-testmon`), flakiness detection by order
  perturbation.

## 1:15–2:15 — Solution

* Observe (PEP 669): per-test file dependencies; deferred local line
  instrumentation.
* Decide: dynamic ∪ static closure ∪ history ∪ flakiness, three named policies, a
  stop rule, an always-run set, a marker for untraceable tests.
* Order by an explainable risk score; report every reason.
* One diagram: `src/pytest_risktest` components and the data flow.
* Policies: `fast`, `balanced`, `safe`; recommend `safe` for CI.

## 2:15–4:45 — Live demo on the presentation laptop

Run `.\scripts\demo.ps1` in the terminal.  Press Enter to advance each step.

1. **Warm-up** — 88 tests run, dependency traces recorded.
2. **Regression** — `feature_02.py` gets a broken weight.
3. **Plan** — `risktest impact --policy safe` shows 8 selected tests and the reason
   for each one.
4. **Selective run** — 8 tests run, 80 are skipped, and the two real failures are
   reported.  This is the safety point: the tool does not hide the regression.
5. **Report** — JSON, Markdown and HTML reports contain changed files, reasons and
   failures.
6. **Fallback** — if the terminal fails, show the screenshots of the same steps.

## 4:45–5:50 — Evaluation

* 36 verified mutations, 4 targets, 3 policies: skip 69–85 %, recall 1.000,
  zero misses, APFD 0.659 → 0.925, 63–85 % of execution time saved, observation
  within 20 %.
* Honest limitations: line granularity cost, process-boundary blind spot with the
  measured mitigation, wall-clock dilution by interpreter start-up.

## 5:50–6:35 — Process and creativity

* Original: evidence fusion with an explicit safety budget, deferred local line
  instrumentation, model-free explainable prioritisation, boundary honesty.
* Process: three sprints, weekly evidence, frozen evaluation contract, two
  benchmark defects found and fixed (R-7), coding-agent contract with review gates.
* Six-member split: repository and release, tests, documentation, evaluation,
  presentation, report.

## 6:35–7:00 — Wrap-up

* What the team would do next: third-party subjects, multi-line faults, freshness
  policy for long-deselected tests.
* Invite questions.  Keep the live demo terminal open in case someone asks for a
  re-run.

## Speaker notes

* Keep one number per slide; the report carries the rest.
* Use the repository itself as the demo environment (the self-hosted target is part
  of the evaluation).
* Do not present future features as part of the constructed software.
* Check the projector resolution before the session.  If the terminal is hard to
  read, increase the font rather than moving the laptop closer.
