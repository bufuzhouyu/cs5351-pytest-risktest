# Presentation and demo video outline (7 minutes)

Format: slides (or HTML) plus a screen recording.  Core goal: the audience
understands the key aspects in seven minutes.  The demo must show the constructed
software, not future work.

## 0:00–1:00 — Background and problem

* The everyday question: "did my change break anything?" → today the answer is
  "run everything".
* Evidence: a verified change affects 9–31 % of the suite, but 100 % is executed.
* The trap: naive skipping hides regressions; a false green is a product-quality
  failure, not a performance one.

## 1:00–2:00 — The technical problem and the challenges

* Which tests *can* a change affect, with evidence?
* Challenges: incomplete observation (first run, stale traces, process
  boundaries), observation cost, explainability, and never hiding a failure.
* Related work in one slide: TIA in build systems, predictive test selection,
  coverage-based selection (`pytest-testmon`), flakiness detection by order
  perturbation.

## 2:00–3:30 — The solution

* Observe (PEP 669): per-test file dependencies; deferred local line
  instrumentation.
* Decide: dynamic ∪ static closure ∪ history ∪ flakiness, three named policies, a
  stop rule, an always-run set, a marker for untraceable tests.
* Order by an explainable risk score; report every reason.
* One diagram: `src/pytest_risktest` components and the data flow.

## 3:30–5:30 — Live demo (recorded)

1. Fresh clone: `pytest -p pytest_risktest.plugin --risktest --risktest-policy=off`
   (warm-up, all tests, traces recorded).
2. Edit one file; `risktest impact --policy safe` (dry run: which tests, and why).
3. `pytest ... --risktest-policy=safe` → show skip rate and the report.
4. Break the file → the failure is still reported (safety).
5. `risktest flaky-check` on a deliberately order-dependent test.
6. Show `benchmark/results/summary.md` and the tracing-strategy figure.

## 5:30–6:30 — Evaluation

* 36 verified mutations, 4 targets, 3 policies: skip 69–85 %, recall 1.000,
  zero misses, APFD 0.659 → 0.925, 63–85 % of execution time saved, observation
  within 20 %.
* Honest limitations: line granularity cost, process-boundary blind spot with the
  measured mitigation, wall-clock dilution by interpreter start-up.

## 6:30–7:00 — Creativity, process and wrap-up

* What is original: evidence fusion with an explicit safety budget, deferred local
  line instrumentation, model-free explainable prioritisation, boundary honesty.
* Process: three sprints, weekly evidence, frozen evaluation contract, two
  benchmark defects found and fixed (R-7), coding-agent contract with review gates.
* What the team would do next: third-party subjects, multi-line faults, freshness
  policy for long-deselected tests.

## Speaker notes

* Keep one number per slide; the report carries the rest.
* Use the repository itself as the demo environment (the self-hosted target is part
  of the evaluation).
* Do not present future features as part of the constructed software.

