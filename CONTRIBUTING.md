# Contributing

This repository is a course project, but it is run like a small product: one
story per branch, one reviewable unit per pull request, evidence in the
repository.

## Workflow

1. Pick a story from `docs/03-requirements.md` (or a risk from
   `docs/06-risk-register.md`) and open an issue with the template.
2. Branch: `sprint-<n>/us-<id>-<short-slug>`.
3. Implement the smallest change that satisfies the acceptance criteria; add or
   update the test that proves it.
4. Run the suite:

   ```powershell
   $env:PYTHONPATH = "src"
   python -m pytest tests -q
   ```

5. Open a pull request with the template.  The CI job must be green; a human
   reviewer must accept the change (see `docs/07-coding-agent-contract.md`).
6. Update `docs/process/weekly-evidence.md`, the sprint document and, if a
   decision was made, `docs/04-architecture.md`.

## Code conventions

* Python 3.12+, standard library only.  No new runtime dependency without an ADR.
* Every module starts with a docstring that explains *why* it exists, not what
  the code obviously does.
* Public functions have type hints; private helpers use a leading underscore.
* Tests follow `tests/test_<module>.py`; end-to-end behaviour goes to
  `tests/test_plugin_integration.py` and runs the plugin in a subprocess.
* Performance claims must be reproducible: add a command to
  `benchmark/` and quote the produced numbers.

## Definition of done

* acceptance criteria of the story are met and provable by a named test;
* the full suite passes locally and in CI;
* the change cannot hide a failing test (or the exception is documented as a risk);
* documentation touched by the change is updated (README, ADR, contract, sprint doc);
* evidence (command + output) is in the pull request.

