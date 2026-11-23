# Live demo cues

On the Windows presentation laptop, run `.\scripts\demo.ps1` from the repository root in PowerShell. Press Enter to advance. The script works on a temporary copy of the benchmark subject.

1. Warm-up: 88 tests, all pass, traces recorded.
2. Change `app/features/feature_02.py` weight to 1.
3. The safe-policy impact plan shows 8 selected tests: 7 direct dependencies and 1 transitive dependency.
4. Run the selected tests: 8 executed, 80 skipped, 2 real failures reported.
5. Show the JSON/Markdown/HTML report.
6. Fallback: show the prepared screenshots.

## Preflight

- From the repository root on the presentation laptop, run `.\scripts\demo.ps1 -NoPause`. Check that the run reports `2 failed` and record the actual output in the rehearsal notes.
- Run `.\scripts\demo.ps1` and press Enter at each prompt. Confirm projection, use an 18–20 pt terminal font, and check that the demo and backups are usable offline.
- Save five screenshots from the same verified run and keep them in an offline folder on the presentation laptop:
  1. `01-warm-up.png` — baseline test summary.
  2. `02-selection-plan.png` — selected tests and reasons.
  3. `03-selected-run.png` — selected-run totals.
  4. `04-failures.png` — the two failure entries.
  5. `05-report.png` — the generated report.

## Demo timing

| Presentation time | Show | Say |
| --- | --- | --- |
| 2:15–2:40 | Warm-up | The baseline runs all 88 tests and records test traces. |
| 2:40–3:00 | Code change | Change the feature weight from 3 to 1 in the temporary subject. |
| 3:00–3:30 | Selection plan | Point to one selected test and its reason. |
| 3:30–4:05 | Selected run and failure list | Read the actual test totals and show the two failure entries. |
| 4:05–4:45 | Report | Show where the report records the selected tests and their results. |

If a demo step stalls, open the matching screenshot and continue through the remaining screenshots. Resume the slides by 4:45.
