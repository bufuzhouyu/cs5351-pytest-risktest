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

## Five-minute presentation

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:40 | Problem and constraints | Running every test after every small change slows feedback. We use dependency evidence to select tests, with safeguards for incomplete traces. |
| 0:40–1:30 | Approach and policies | pytest records which files each test executes. RiskTest combines those traces with the import graph. The safe policy follows transitive dependencies and keeps tests whose evidence is missing. |
| 1:30–1:50 | Warm-up and mutation | All 88 tests pass in the temporary subject. We change one feature's weight from 3 to 1. |
| 1:50–2:15 | Selection plan | Safe selects eight tests. Seven directly depend on the changed file and one is included through the import graph. |
| 2:15–2:45 | Selective run and failures | Eight tests run and 80 are deselected. Two tests detect the intentional regression. |
| 2:45–3:00 | Report | Point to the changed file, selection reasons, and two failing tests. |
| 3:00–4:15 | Evaluation and limits | Use the team's frozen benchmark figures. Mention trace overhead and the subprocess blind spot. |
| 4:15–5:00 | Conclusion | Summarize the selection trade-off and hand over to Q&A. |
| 5:00–7:00 | Q&A | Keep the report open for questions about selection evidence. |

If the terminal stalls, open the matching backup image. Return to the slides by 3:00 and begin Q&A at 5:00.

## Q&A prompts

- **Why were eight tests selected?** Seven directly depended on the changed file, and one was included through the import graph.
- **Why did two tests fail?** The intentional weight change broke two assertions. The full warm-up passed before the change.
- **When can traces miss dependencies?** Subprocess execution can be invisible to the tracer. Mark affected tests to always run.
