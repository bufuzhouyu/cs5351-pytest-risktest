# Offline presentation rehearsal notes

Format: five-minute presentation with slides and a live demo, followed by two minutes of Q&A.

The team will schedule its own practice and presentation setup. The macOS
preflight below records the technical verification completed for this handoff.

## Timing supplied by the presenter

These timings are unverified. Talk duration includes the demo. Q&A is tracked
separately and no Q&A timing was supplied.

| Round | Talk duration | Demo duration | Issue reported |
| --- | --- | --- | --- |
| 1 | 8:00 | 5:00 | The demo script was too long. |
| 2 | 7:00 | 3:00 | The conclusion repeated earlier points. |
| 3 | 5:00 | 2:00 | No issue was reported. |

## Target timing

- 0:00–0:40 problem and constraints
- 0:40–1:30 solution
- 1:30–3:00 live demo
- 3:00–4:15 evaluation and limits
- 4:15–5:00 conclusion
- 5:00–7:00 Q&A

## Backup plan

- If the terminal fails, continue from the matching screenshot in the offline backup folder.
- If projection fails, give the spoken walkthrough and have the slides and screenshots ready to reopen once projection is restored.
- If demo data is missing, use the screenshots from a verified run.

## Verification

- [x] Capture macOS preflight output, including the expected `2 failed` result.
- [ ] Time the five-minute talk and two-minute Q&A during team practice.
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

- Use the five-minute rundown in [demo-cues.md](demo-cues.md) for the presentation.
- The existing deck cites the 36-run baseline. M4 PR #13 reports 48 runs. Confirm the team's frozen figures before presenting.
