# IEEE TSE report checklist

Status: content audit completed 2026-11-27 against `report-draft.md` on
`sprint-3/m6-report-scaffold`.  Remaining work is listed under **Remaining gaps**.

## Structure

- [x] Title, team name (`Code Group 18 Default`) and project number (18)
- [ ] Project number 18 verified against Canvas (see the caveat in
      `docs/09-topic-introduction-for-ta.md`)
- [x] Six members with student IDs (not EID)
- [x] Abstract is 149 words (limit 150)
- [x] Body is 9 880 words before the reference list (target about 10 000)
- [x] Introduction, related work and preliminaries
- [x] Solution with algorithms, architecture decisions and figures
- [x] Software process: three sprints, evidence ownership and burndown
- [x] Evaluation with the frozen 48-run metrics
- [x] Conclusion
- [x] References in IEEE style

## Data consistency

- [x] Every number in the report is copied from `benchmark/results/summary.md`
      at the frozen commit, not carried over from an earlier draft
- [x] Frozen figures used: 48 runs (4 targets × 4 mutations × 3 policies);
      APFD tool 0.925 / baseline 0.521; skip rate 73.1 % safe, 74.6 % balanced,
      85.2 % fast; time saved 18.5 / 19.7 / 25.2 %; work saved 67.5 / 69.4 / 85.3 %
- [x] File-granularity overhead reported per target: 6.47–12.87 % on the three
      generated targets, 28.28 % on the self-hosted target
- [x] RQ2 is reported as partially met: generated targets pass the 20 % threshold,
      the self-hosted target exceeds it
- [x] Line-granularity overhead reported as 1 158–1 293 % (generated targets)
- [x] Test counts consistent: 121 in the repository suite, 103 in the self-hosted
      benchmark target (88 in each generated target)
- [x] `time_saved` (wall clock) and `work_saved` (test execution work) are never
      used interchangeably in the abstract, §1.4, §6 or §8
- [x] Figures in `docs/report/figures/` are the regenerated post-rerun versions
- [ ] Presentation deck still cites the 36-run baseline
      (`docs/report/rehearsal-notes.md` flags this) — M5 to confirm

## People and evidence

- [x] Six biographies are present in `docs/team/` or approved PRs #22/#24
- [ ] 张力元's bio still lacks major/year
- [x] All six members have a self-reflection (M4 and M5 are in PRs #24 and #22)
- [ ] Merge approved PRs #22 and #24 so the reflections are on `main`
- [x] `contribution-table.csv` uses the accepted productive-hour allocation
- [x] Table arithmetic verified: totals 40/40/32/36/30/40, mean 36.333, shares
      1.101/1.101/0.881/0.991/0.826/1.101, summing to 6.001 ≈ 6.00
- [x] §10 states the measure explicitly (productive hours) and cites
      `docs/process/evidence-ownership.md` as the source
- [x] Weekly evidence follows `docs/process/evidence-ownership.md`; weeks 4, 6, 7,
      9 and 10 stay empty by decision
- [ ] Week 13 row to be recorded by M6 after the final submission
- [ ] Burndown actuals for weeks 6–13 are still missing (only weeks 1–5 filled)
- [ ] Standing meeting minutes are still empty
- [x] Risk register and coding-agent contract are referenced

## Figures and tables

- [x] Every figure is numbered and referenced in the text
- [x] Every table is numbered and referenced in the text
- [x] Figure numbering is continuous (Figs. 1–8)
- [x] Table numbering is continuous (Tables I–X, plus Table A1 in the appendix)
- [x] All eight generated figures are used
- [ ] Figures render at readable size in the final Word/PDF layout
- [ ] Captions are checked against the final layout

## References

- [x] Every entry in the reference list is cited in the body text
- [x] Every in-text citation has a matching entry (no orphan citations)
- [x] Citations are numbered in order of first appearance
- [x] Each entry has author, title, venue, year and a URL/pages/DOI where applicable

## Final checks

- [ ] Report uses the IEEE TSE Word or LaTeX template
- [ ] Page count and formatting match the template
- [ ] PDF opens correctly and fonts are embedded
- [ ] PDF is under the submission size limit
- [x] Repository link and release tag are included
- [ ] Full-text search for `待填写`, `待补充`, `TODO`, `??` returns nothing
- [ ] Final read-through after typesetting

## Remaining gaps

1. Merge approved PRs #22 (M5 reflection) and #24 (M4 reflection).
2. Add 张力元's major/year to `docs/team/zhangliyuan.md`.
3. Verify project number 18 against Canvas.
4. Fill burndown actuals for weeks 6–13 and the standing meeting minutes, or
   record explicitly why those weeks have no separate evidence.
5. Typeset the report in the IEEE template and export the PDF.
6. `docs/02-open-source-base-and-related-work.md` and `docs/04-architecture.md`
   still quote pre-rerun numbers (for example the old −2.3 % local-line result).
   The report itself uses the frozen values; those two supporting documents need
   a separate consistency update.
