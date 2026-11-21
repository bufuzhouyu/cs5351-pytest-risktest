# Two-week plan to the presentation

Dates assume a Friday 2026-11-20 start and a presentation in the week beginning
2026-11-30. Adjust the presentation day if the course announces a different slot.

## Week 1 (11/20–11/29): repository, identities and one real PR per member

| Date | Activity | Owner | Evidence |
| --- | --- | --- | --- |
| Fri 11/20 | Create GitHub repository, push `main`, invite five members and the TA | M1 | repository URL, collaborator list |
| Fri 11/20 | Each member sets name and GitHub no-reply email, clones, adds their row to `TEAM.md` | ALL | six commits, one per member |
| Sat 11/21 | Create six issues from the user-story template and assign owners | M1 | issue numbers |
| Sat 11/21 | Protect `main`: require PR, one approval, CI status check | M1 | branch protection screenshot in weekly evidence |
| Mon 11/23 | Midpoint check: every member has a branch and at least one commit | M1 | `scripts/check-team-records.ps1` output |
| Tue 11/24 | First pull requests opened and reviewed | ALL | six PR links |
| Wed 11/25 | Merge first PRs, fix CI failures | ALL | green CI |
| Thu 11/26 | Second task or follow-up commit for members who need more evidence | M2–M6 | commits and PR reviews |
| Fri 11/27 | Slide content freeze, benchmark numbers frozen | M4, M5 | updated results and deck |
| Sat 11/28 | Full rehearsal with the deck and the demo, timed | ALL | rehearsal notes, action list |
| Sun 11/29 | Fix rehearsal issues, update weekly evidence and contribution hours | ALL | evidence table, hours |

## Week 2 (11/30–12/06): freeze, record and submit

| Date | Activity | Owner | Evidence |
| --- | --- | --- | --- |
| Mon 11/30 | Code freeze, final test run, tag release `v0.1.0` | M1, M2 | tag, CI run, test output |
| Mon 11/30 | Rehearse the live demo with `scripts/demo.ps1` on the presentation laptop | M5 | successful dry run, timing note |
| Tue 12/01 | Move the report into the IEEE TSE template, insert figures, fill bios | M6, ALL | report PDF |
| Wed 12/02 | Final rehearsal, check timing and transitions | ALL | checklist |
| Thu 12/03 | Submit slides, report and repository link | M1 | submission confirmation |
| Fri 12/04 | Buffer for corrections | ALL | — |

## Member assignments

| Member | Primary task | Secondary task |
| --- | --- | --- |
| M1 Team lead | repository, branch protection, CI, release, final integration | weekly evidence and contribution table |
| M2 Test owner | 10+ new tests for selector, CLI and reporting | coverage summary in the PR |
| M3 Docs owner | Chinese README, troubleshooting, link check | topic introduction for the TA |
| M4 Evaluation owner | re-run benchmark with 4 subjects and 4 mutations | update figures and the evaluation section |
| M5 Presentation owner | final deck, rehearsal, live demo | timing notes and backup screenshots |
| M6 Report owner | IEEE TSE template, bios, references | risk register and process section |

## Definition of done before submitting

* all six members appear in `git shortlog -sne` and in GitHub **Contributors**;
* each member has at least one merged pull request and one review;
* CI is green on `main`;
* the live demo fits the seven-minute slot and runs on the presentation machine;
* the report has all student bios, self-reflections and the contribution table;
* `docs/process/weekly-evidence.md` has a row for every week up to submission.
