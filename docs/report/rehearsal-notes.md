# Offline presentation rehearsal notes

Presentation: 7 minutes, slides plus a live terminal demo. No video.

| Rehearsal | Date | Room/equipment | Total time | Demo time | Problems | Fix |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

## Target timing

- 0:00–0:35 opening
- 0:35–1:15 problem and constraints
- 1:15–2:15 solution
- 2:15–4:45 live demo
- 4:45–5:50 evaluation
- 5:50–6:35 limits and process
- 6:35–7:00 close

## Backup plan

- If the terminal fails, continue from the matching screenshot in the offline backup folder.
- If projection fails, give the spoken walkthrough and have the slides and screenshots ready to reopen once projection is restored.
- If demo data is missing, use the screenshots from a verified run.

## Verification

- [ ] Record actual total and demo times for three complete rehearsals, including problems and fixes.
- [ ] Complete a rehearsal within 7:00.
- [ ] Record the command output, including the expected `2 failed` result.
- [ ] Verify the five backup screenshots open offline on the presentation laptop.
- [ ] Check projection and terminal font size on the presentation laptop during the November 30 walkthrough.

## macOS preflight — November 23, 2026

Ran the Python steps from `scripts/demo.ps1` with Python 3.12.16 and pytest 9.2.0 in a temporary copy of `benchmark/subjects/subject_01`. Run all steps from the temporary subject root so collection and the impact command use the same test IDs.

```sh
# Start at the repository root with Python 3.12 and pytest available.
repo="$PWD"
work="$(mktemp -d /private/tmp/cs5351-m5-demo.XXXXXX)"
cp -R "$repo/benchmark/subjects/subject_01/." "$work/"
cd "$work"
export PYTHONPATH="$repo/src:$work" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1
python -m pytest -q -p no:cacheprovider -p pytest_risktest.plugin \
  --risktest --risktest-policy=off --risktest-report=.risktest/warm.json tests
perl -pi -e 's/WEIGHT = \d+/WEIGHT = 1/' app/features/feature_02.py
python -m pytest_risktest impact --root "$work" --policy safe --limit 8 tests
python -m pytest -q -p no:cacheprovider -p pytest_risktest.plugin \
  --risktest --risktest-policy=safe --risktest-report=.risktest/run.json tests
python -m pytest_risktest report --report .risktest/run.json --format markdown
```

The selective pytest command is expected to exit with status 1 because the
temporary change causes two test failures.

```text
Warm-up: 88 passed
Safe impact plan: 8/88 selected, 80 deselected (90.9%)
Selection reasons: 7 changed-dependency, 1 transitive-dependency
Selective run: 2 failed, 6 passed, 80 deselected
Failing tests: test_feature_02.py::test_compute and test_feature_02.py::test_normalize_total
Reports: run.json, run.md, run.html
```

The PowerShell runs and equipment checks on the presentation laptop are pending.

Five offline PNGs were rendered from the captured macOS output and saved in
the local `demo-backup/` folder alongside the raw logs and HTML report. Open
them in filename order. Verify the files on the presentation laptop before
the session.

## Deck and narration

- Reviewed the ten-slide deck and the seven-minute narration for the live-demo handoff. Start the demo at 2:15 and return to the evaluation slide by 4:45.
- The current deck still uses the 36-run evaluation baseline. The M4 rerun in PR #13 reports 48 runs. Confirm which figures the team freezes and align the deck and narration before the November 28 rehearsal.
- Use the first rehearsal to measure the full talk, the second to practice switching to the offline visuals, and the third to verify the final timing after any cuts. Record the actual duration and any issues after each run.
