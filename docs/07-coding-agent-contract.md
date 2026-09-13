# Coding-agent use contract

Based on the course guidance ("Delegate bounded tasks with repository context and
explicit constraints; require tests, rationale, and a reviewable pull request;
team members own, challenge, and may reject every output") and on GitHub's
documentation for coding agents and status checks.

## Principles

1. **Bounded task.**  An agent receives one story or one defect with an explicit
   scope: files it may touch, files it must not touch, and the acceptance test it
   has to make pass.
2. **Repository context.**  Every task includes the relevant documents
   (`docs/03-requirements.md`, the ADRs, the evaluation contract) and the current
   failing test or measurement.
3. **Explicit constraints.**  No new runtime dependency; no change to the frozen
   metrics; no change to the public option names; tests must exist for new
   behaviour; performance claims must come with a measurement command.
4. **Evidence over assertion.**  An agent's claim is accepted only with
   (a) the command that reproduces it, (b) the produced numbers or test output,
   (c) the diff it applies.
5. **Human ownership.**  A human reviewer can reject any output.  The team member
   who merges is accountable for the change, and the reasoning must be
   understandable without the agent's chat history.
6. **One change, one reviewable unit.**  Each agent task ends as one commit or
   pull request that links the issue, the acceptance test, and the evidence.

## Task template

```
Story:            US-3 (docs/03-requirements.md)
Goal:             always select tests whose dependencies are unknown
Scope:            src/pytest_risktest/selector.py,
                  tests/test_selector.py
Do not touch:     docs/05-evaluation-contract.md, benchmark/results/**
Constraints:      no new dependency; keep the public option names;
                  keep plan_selection's signature backwards compatible
Evidence needed:  new unit test names + `pytest tests/test_selector.py -q`
                  output + the reason histogram of one end-to-end run
Definition of done: the acceptance test of US-3 passes; the full suite passes;
                  the change is explained in one paragraph in the PR
```

## Review checklist applied to every agent-produced change

| Check | Question |
| --- | --- |
| Scope | Does the diff stay inside the declared scope? |
| Test | Is there a test that fails before and passes after? |
| Rationale | Is the reason for the change understandable without the agent transcript? |
| Evidence | Are the commands and their outputs included, and do they match the claim? |
| Contract | Are the frozen metrics, targets and thresholds untouched? |
| Safety | Could the change hide a failure or break a user's run? |
| Style | Does it follow the surrounding code and the project vocabulary? |

## How this project actually used agents

| Task type | Delegated to an agent | Kept by the team |
| --- | --- | --- |
| Scaffolding a module from a written specification | yes | specification, review, acceptance |
| Writing unit tests for an existing function | yes | choosing which properties matter |
| Running the benchmark and summarising numbers | yes | freezing the contract, interpreting the result, deciding the next step |
| Choosing the selection policy default | no (agent produced the options and measurements) | the decision, recorded as ADR-3 |
| Writing the report's self-reflection and contribution sections | no | each student |

Status checks (`.github/workflows/ci.yml`) make the required evidence visible at
the pull request: the test job must be green before a change is merged.

