# Weekly repository evidence

The course requires the repository to capture the team's weekly activities.  One
row per week per owner; a row is only valid if it links the issue, the change and
the evidence produced that week.  Weeks that are still in the future are left
blank on purpose — the team fills them as the work happens.

| Week | Date | Owner | Issue | Change (commit/PR) | Evidence produced | Risk/decision |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-08 | 赵尊 (M1) | #1 team formation | — | team list, project name, repository created | — |
| 2 | 2026-09-14 | ALL | #2… | initial import: plugin, monitor, graph, store, selector, tests | 96 tests passing; benchmark harness; evaluation contract frozen | R-7 found and fixed (benchmark validity) |
| 3 | 2026-09-21 | 肖宇 (M3) | [#8](https://github.com/bufuzhouyu/cs5351-pytest-risktest/issues/8) | [PR #4](https://github.com/bufuzhouyu/cs5351-pytest-risktest/pull/4)（`f9086bf`）、[PR #14](https://github.com/bufuzhouyu/cs5351-pytest-risktest/pull/14) | 8 项排错说明；中文 README 的 17 处相对链接在仓库副本中均可解析；状态查询显示 121 个测试有依赖记录 | 张力元批准，GitHub 检查 5/5 通过，文档于 2026-11-23 合并 |
| 4 | | | | | | |
| 5 | 2026-10-05 | 代佳乐 (M2) | #1 M2 regression tests | PR #3 (commits `7f5f57a`, `5b87a21`, `ee764c7`) | `tests/test_selector_extra.py` 新增 22 个用例；完整套件 121 passed（基线 99）；覆盖率 62%，排除子进程模块后 89.6%；`docs/process/test-report.md` 填真实数字 | 未修改 `src/`；未发现缺陷 |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | 2026-11-22 | 张力元 (M4) | [#9](https://github.com/bufuzhouyu/cs5351-pytest-risktest/issues/9) | [PR #13](https://github.com/bufuzhouyu/cs5351-pytest-risktest/pull/13), commit [`34c6da4`](https://github.com/bufuzhouyu/cs5351-pytest-risktest/commit/34c6da4) | [跑测记录](benchmark-rerun-2026-11.md)，4 个目标 × 4 个变异 × 3 种策略，48 次运行漏报为 0；完整测试 121 passed | 默认 seed 出现重复变异，使用 20260102 |
| 9 | | | | | | |
| 10 | | | | | | |
| 11 | 2026-11-23 | 庄志洋 (M5) | [#10](https://github.com/bufuzhouyu/cs5351-pytest-risktest/issues/10) | [PR #15](https://github.com/bufuzhouyu/cs5351-pytest-risktest/pull/15)、[PR #18](https://github.com/bufuzhouyu/cs5351-pytest-risktest/pull/18) | 5 分钟讲解 + 2 分钟 Q&A 的演示稿与演示脚本；三次彩排时长（8:00、7:00、5:00，为 presenter 自报，`docs/report/rehearsal-notes.md` 标注 unverified）；备份截图和 11/30 投影检查待完成 | 线下 Pre，不录视频；本行由 M1 代录，待 M5 本人确认 |
| 12 | 2026-11-22 | 赵尊 (M1) | [#6](https://github.com/bufuzhouyu/cs5351-pytest-risktest/issues/6) | [PR #5](https://github.com/bufuzhouyu/cs5351-pytest-risktest/pull/5)（`63eaea8`、`ca96a34`） | CI 5/5 全绿（Python 3.12/3.13 × Ubuntu/Windows + benchmark smoke）；tag `v0.1.0`；6 个 Issue 已创建并指派；补上 pytest 安装步骤修复 CI | 分支保护已生效；待 PR #5 审批合并 |
| 13 | | | | | | |

## Standing meeting evidence

No separate standing meeting minutes were recorded.  Weekly activity and
decisions are documented in the table above; no minutes have been invented.

