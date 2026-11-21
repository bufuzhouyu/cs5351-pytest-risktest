# GitHub upload and per-member work records

This guide is written for a team of six with roughly two weeks left before the
presentation. It covers the repository setup, the per-member git identity, the
issue and pull-request workflow that produces reviewable evidence, and the checks
the team should run before submission.

> The course asks for weekly evidence and a relative-contribution table. GitHub
> commits and pull requests are evidence, but they are not a substitute for the
> team's own record of hours and decisions. Do not create commits on behalf of a
> member who did not do the work. A fabricated history is easy to spot (trivial
> diffs, identical timestamps, no reviews) and is academic misconduct.

## 0. Current state (2026-11-20)

* The repository has six commits, all authored as `CS5351 Team <team@example.com>`.
* There is no git remote yet.
* The branch is `main`.
* Untracked files: `README.zh-CN.md`, `docs/09-topic-introduction-for-ta.md`
  and `out/` (generated demo report).

Recommended handling:

1. Keep the existing history. Re-attributing it to members who did not do that
   work would be dishonest. Explain in the first weekly-evidence row that the
   initial scaffold came from a team working session.
2. From now on, every member commits with their own name and GitHub-linked email.
3. The team lead commits the untracked documents and adds `out/` to `.gitignore`.
   That is the lead's first real commit.
4. If a specific member really drove part of the initial work, name them in the
   weekly evidence and the contribution table instead of rewriting authorship.

## 1. Create the GitHub repository (team lead, 10 minutes)

Option A: web interface (no extra tools).

1. Sign in to GitHub, open <https://github.com/new>.
2. Repository name: `cs5351-pytest-risktest`.
3. Visibility: private is fine. If the course requires a public repository, choose
   public. If it is private, invite the TA and lecturer later.
4. Do **not** initialise with README, .gitignore or licence. The local repository
   already has them.
5. Create the repository, then add the remote:

```powershell
cd "D:\课程\CS5351_Software-Engineering\project"
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

Authentication options on Windows:

* Git Credential Manager opens a browser the first time you push. Sign in and
  approve. This is the easiest option.
* Personal Access Token: use the token as the password when git asks.
* GitHub Desktop: sign in, then add the existing local repository and publish it.

Option B: GitHub CLI (optional).

```powershell
winget install --id GitHub.cli
gh auth login
gh repo create cs5351-pytest-risktest --private --source . --remote origin --push
```

## 2. Invite the six members (team lead, 5 minutes)

GitHub repository, **Settings → Collaborators → Add people**. Add all five other
members with their GitHub accounts. If the course requires it, also add the TA and
the lecturer as read-only collaborators (or use an organisation with a team).

Then create **Settings → Branches → Add branch protection rule** for `main`:

* Require a pull request before merging.
* Require one approval.
* Require status checks to pass (select the CI job from `.github/workflows/ci.yml`).
* Do not allow force pushes.

This is what makes the issue → pull request → review chain visible at submission.

## 3. Every member: one-time setup (5 minutes each)

Install Git for Windows if needed: <https://git-scm.com/download/win>.

```powershell
git config --global user.name "Your Real Name"
git config --global user.email "12345678+your-github-username@users.noreply.github.com"
```

The email must be one that GitHub associates with the account, otherwise the
commits will not link to the member's profile. The `+` address is a GitHub no-reply
address and works well for coursework. Get the exact address from GitHub:
**Settings → Emails → Keep my email addresses private**.

Clone the repository:

```powershell
cd D:\课程
git clone https://github.com/<owner>/<repo>.git cs5351-project
cd cs5351-project
git config user.name "Your Real Name"
git config user.email "12345678+your-github-username@users.noreply.github.com"
```

The repository-level `git config` (without `--global`) overrides a shared account
on a lab machine and is the safest choice for this project.

## 4. The working loop that produces records

Every task follows the same five steps. Each member should own at least one issue
and one pull request before the presentation.

1. **Issue** — open it with the "User story" template. State the acceptance
   criteria and the evidence you will produce.
2. **Branch** — name it after the sprint and the issue:

```powershell
git switch -c sprint-3/us-7-your-name
```

3. **Commit** — make small, meaningful commits. One commit per logical change.
   Include a linked issue in the message:

```powershell
git add -A
git commit -m "US-7: add flaky-check regression test (closes #21)"
git push -u origin HEAD
```

4. **Pull request** — open it on GitHub. In the description write:

```text
Closes #21
Evidence: python -m pytest tests -q -> 99 passed
Contract: docs/05-evaluation-contract.md unchanged
```

5. **Review and merge** — another member reviews, checks that the tests ran in CI,
   leaves one substantive comment, approves, and merges. The reviewer also gets a
   record, but the review must be real.

A useful measure of a real task: it changes behaviour or evidence, has a test or
measurement, and another person can understand it without asking the author.

## 5. Two-week split for six members

The detailed day-by-day plan is in `docs/process/two-week-plan.md`. Each role below
is a real deliverable, not a token commit.

| Member | Role | Deliverable | Acceptance evidence |
| --- | --- | --- | --- |
| M1 | Team lead / release | Repo, protection rules, CI green, release notes, final integration PR | CI status, merged PR, tag `v0.1.0` |
| M2 | Test and quality | 10 or more new tests for selector, CLI and reporting edge cases | CI passes, coverage summary in the PR |
| M3 | Documentation | Chinese README, troubleshooting section, corrected links | `README.zh-CN.md`, docs diff |
| M4 | Evaluation | Re-run the benchmark with 4 subjects and 4 mutations, refresh tables and figures | New `benchmark/results/summary.md` plus a short interpretation |
| M5 | Presentation | Final deck, timed rehearsal, live demo | Deck commit, rehearsal timing note, successful live run |
| M6 | Report | Move the draft into the IEEE TSE template, bios, contribution table, references | Formatted report, section checklist |

Every member must also write their own bio and self-reflection. Those sections
cannot be delegated.

## 6. Verify the records before submission

Run the helper from the repository root:

```powershell
.\scripts\check-team-records.ps1 -Members "Member One","Member Two","Member Three","Member Four","Member Five","Member Six"
```

It prints the commit count per author and warns about members with no commits. On
GitHub, also check **Insights → Contributors** and **Pull requests → Closed** to
confirm that every member has at least one merged pull request.

Weekly evidence: update `docs/process/weekly-evidence.md` every week with the
issue number, the pull request link, the commit hash and the evidence produced.
The final report's contribution table should use the same data.

## 7. Common problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Commits show a generic name on GitHub | `user.name` or `user.email` is not the member's GitHub identity | Set the repository-level config again and make new commits |
| Commits show "unverified" | The email is correct but not linked to the account | Use the GitHub no-reply address; it still links the author |
| `push` asks for a password | GitHub no longer accepts account passwords | Use Git Credential Manager, a PAT, or GitHub Desktop |
| CI fails on Windows only | Path or encoding assumption | Set `PYTHONIOENCODING=utf-8`; the tests already do this for child processes |
| The repository grows quickly | Generated reports or caches committed | Add `out/`, `.risktest/`, `.pytest_cache/` to `.gitignore` |
| Desktop warns about LF/CRLF conversion | Global `core.autocrlf=true` conflicts with LF files | Keep `.gitattributes` (`text eol=lf`, `*.ps1 eol=crlf`, binaries `binary`) and the repo-local `core.autocrlf=false`; commit normally, never discard changes |
| A member has commits but no reviews | Only coding was counted | Have them review one pull request and record it |

## 8. Presentation-week checklist

* Code freeze on Monday of presentation week. After that, only documentation and
  bug fixes with tests.
* Rehearse the live demo with `scripts/demo.ps1` on the presentation laptop.
  Keep the talk and the demo inside seven minutes.
* Run the full suite and paste the result into the pull request and the report.
* Export the final report to PDF and check that all figures and tables render.
* Confirm that all six members appear in **Insights → Contributors** and in the
  contribution table.
