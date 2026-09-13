## Requirement

Closes #<!-- issue number -->

Story / NFR: `US-<!-- n -->` or `NFR-<!-- n -->` in `docs/03-requirements.md`

## What changed

<!-- one paragraph: the problem, the approach, why this approach -->

## Evidence

* Acceptance test added/changed: `tests/...::...`
* Command and result:

```
python -m pytest tests -q   ->  95 passed
```

* Measurement (only if the change claims a performance or quality effect):

```
python benchmark/run_bench.py --subjects 1 --mutations 1
```

## Contract check

* [ ] `docs/05-evaluation-contract.md` metrics, targets and thresholds unchanged
  (or the change is described and dated in the sprint log)
* [ ] no new runtime dependency (`pyproject.toml` `dependencies` still empty)
* [ ] public option names unchanged, or the change is documented in `README.md`
* [ ] the change cannot hide a failure (always-run set / stop rules still hold)

## Review

* Rationale understandable without the author's chat history: yes/no
* Reviewer may reject: this PR is only merged after a human review

