# IEEE TSE report checklist

Status: scaffolding created 2026-11-26 by M1; audited and extended by M6 on
2026-11-26 against `sprint-3/m6-report-scaffold` @ `2803f0a`. Measured gaps are
listed at the bottom.

## Structure

- [ ] Title, team name (`Code Group 18 Default`) and project number (18)
- [ ] Project number 18 verified against Canvas (see the caveat in
      `docs/09-topic-introduction-for-ta.md`)
- [ ] Six members with student IDs (not EID)
- [ ] Abstract within 150 words (measured 203 words on 2026-11-26 — must be cut)
- [ ] Body length about 10 000 words (measured 7 249 words on 2026-11-26)
- [ ] Introduction (1–1.5 pages)
- [ ] Related work (about 1 page)
- [ ] Preliminaries (1–2 pages)
- [ ] Solution (2–3 pages) with algorithms and figures
- [ ] Software process: three sprints and burndown
- [ ] Evaluation (2–5 pages) with the frozen metrics
- [ ] Conclusion (1 page)
- [ ] References in IEEE style

## Data consistency

- [ ] Every number in the report is copied from `benchmark/results/summary.md`
      at the frozen commit, not carried over from an earlier draft
- [ ] Frozen figures used: 48 runs (4 targets x 4 mutations x 3 policies);
      APFD tool 0.925 / baseline 0.521; skip rate 73.1 % safe, 74.6 % balanced,
      85.2 % fast; time saved 18.5 / 19.7 / 25.2 %; work saved 67.5 / 69.4 / 85.3 %
- [ ] File-granularity overhead reported per target: 6.47–12.87 % on the three
      generated targets, 28.28 % on the self-hosted target
- [ ] RQ2 verdict re-checked against the 20 % threshold — the self-hosted target
      exceeds it, so the claim "within 20 % on every target" must be rewritten
- [ ] Line-granularity overhead reported as 1 158–1 293 % (generated targets)
- [ ] Test counts consistent: 121 in the repository suite, 103 in the self-hosted
      benchmark target (88 in each generated target)
- [ ] `time_saved` (wall clock) and `work_saved` (test execution work) are never
      used interchangeably in the abstract, §1.4, §6 or §8
- [ ] Figures in `docs/report/figures/` are the regenerated post-rerun versions
- [ ] The presentation deck still cites the 36-run baseline
      (`docs/report/rehearsal-notes.md` flags this) — M5 to confirm

## People and evidence

- [ ] Six bios in `docs/team/` are complete (five merged on `main`; 周浩然 in this
      PR). 张力元's bio still lacks major/year, technical background and interests
- [ ] Each member adds a self-reflection: 赵尊 and 周浩然 done, 庄志洋 in PR #22,
      代佳乐 / 肖宇 / 张力元 still to write their own
- [ ] `contribution-table.csv` hours confirmed by each member — the current
      numbers are the lead's proposal recorded in
      `docs/process/evidence-ownership.md`, which asks every member to confirm
      or adjust their own row before the final report
- [ ] Table arithmetic verified: totals 40/40/32/36/30/40, mean 36.333, shares
      1.101/1.101/0.881/0.991/0.826/1.101, summing to 6.001 ≈ 6.00
- [ ] §10 states the measure explicitly (productive hours) and applies it to all
      six members, citing `docs/process/evidence-ownership.md` as the source
- [ ] Weekly evidence follows the ownership table in
      `docs/process/evidence-ownership.md`; weeks 4, 6, 7, 9 and 10 stay empty by
      decision — do not invent rows
- [ ] Week 13 row recorded by M6 after the final submission
- [ ] Burndown actuals cover weeks 6–13 (currently only weeks 1–5 are filled)
- [ ] Standing meeting minutes filled for the weeks the team actually met
- [ ] Risk register and coding-agent contract are referenced

## Figures and tables

- [ ] Every figure is numbered and referenced in the text
- [ ] Every table is numbered and referenced in the text
- [ ] Figure numbering is continuous, with no gaps or duplicates
- [ ] All eight generated figures are either used or deliberately dropped
      (`benchmark-time-saved.svg` and `benchmark-work-saved.svg` are unused)
- [ ] Figures from `docs/report/figures/` render at readable size
- [ ] Captions are complete and consistent

## References

- [ ] Every entry in the reference list is cited in the body text
- [ ] Every in-text citation has a matching entry (no orphan citations)
- [ ] Citations are numbered in order of first appearance
- [ ] Each entry has author, title, venue, year and pages/DOI where applicable
      ([5], [6] and [14] are currently missing publication details)

## Final checks

- [ ] Report uses the IEEE TSE Word or LaTeX template
- [ ] Page count and formatting match the template
- [ ] PDF opens correctly and fonts are embedded
- [ ] PDF is under the submission size limit
- [ ] Repository link and release tag are included
- [ ] Full-text search for `待填写`, `待补充`, `TODO`, `??` returns nothing

## Resolved since the scaffolding commit

* Team name `Code Group 18 Default` and project number 18 filled in `TEAM.md`,
  both READMEs, the report cover line, `docs/00-assignment-mapping.md` and
  `docs/09-topic-introduction-for-ta.md`.
* `contribution-table.csv` populated for all six members and three sprints.
* Weekly evidence ownership documented in `docs/process/evidence-ownership.md`.
* M4 benchmark rerun merged (PR #13), so the frozen numbers and figures are final.

## Known gaps (measured 2026-11-26)

1. `report-draft.md` body still quotes the pre-rerun results (36 runs, APFD
   baseline 0.659, "overhead within 20 %") while the figures were regenerated
   from the frozen 48-run results — about a dozen numbers across the abstract,
   §1.4, §6, §7 and §8 must be updated.
2. No figure or table in the draft is numbered, and none is referenced in the
   text; two of the eight figures are unused.
3. None of the fifteen references is cited in the body text.
4. Abstract is 203 words against a 150-word limit; body is 7 249 words against
   roughly 10 000.
5. Contribution hours are the lead's proposal and have not been confirmed by the
   six members yet.
6. Burndown actuals stop at week 5 and the standing meeting minutes table is
   empty, so §5 cannot yet evidence three complete sprints.
7. Three members (代佳乐, 肖宇, 张力元) have no self-reflection, and 张力元's bio
   is missing three fields.
8. No IEEE-template layout and no PDF exist yet.
