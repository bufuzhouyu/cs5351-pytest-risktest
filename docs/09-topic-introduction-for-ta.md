# Project topic introduction (for TA review)

Milestone 0 of the course asks the team to email the TAs and the lecturer the team
list, the project number and the chosen project.  This document holds the short
introduction that was sent, so the topic request itself is part of the repository
evidence.

The member list is complete.  Only `<team name>` and `<project number>` remain to
be confirmed before this email is sent.

---

## Email (send this)

**Subject:** CS5351 project topic for review — Team `<team name>` (project `<project number>`)

Dear TA,

Our team is Team `<team name>` (project `<project number>`; members:
Zhao Zun 赵尊 72610823, Dai Jiale 代佳乐 72612080, Xiao Yu 肖宇 72610896,
Zhang Liyuan 张力元 72610454, Zhuang Zhiyang 庄志洋 72610571,
Zhou Haoran 周浩然 72610429).
We would like to confirm our project topic before implementation starts.

**Title:** Risk-Aware Test Selection, Prioritisation and Flakiness Triage for pytest

**Problem.** When a developer changes a small part of a Python project, the only
safe answer today is to run the whole test suite, so feedback time grows with the
size of the suite instead of the size of the change. Skipping tests naively is
worse: a missed regression is reported as green.

**Base and originality.** We build on **pytest** (open source, plugin API; we do
not modify its source code) and contribute our own algorithms: (i) per-test
dependency observation using PEP 669 `sys.monitoring`, with a deferred
per-code-object line-tracing strategy; (ii) fusion of observed execution, the
static import closure, run history and flakiness into named, auditable selection
policies (`fast` / `balanced` / `safe`); (iii) an explainable risk ordering; and
(iv) differential flakiness detection.

**Safety.** Tests with unknown dependencies, previous failures or flaky
suspicions, and any test marked `@pytest.mark.risktest_always`, are always
executed; a stop rule caps how much of the suite may be skipped; and a change to
build/test configuration forces a full run.

**Non-functional requirements** (each with an architectural design option and its
measured rationale): NFR-1 performance — observation overhead below 20 % at file
granularity (measured −8.5 % … +16.7 %); NFR-2 reliability — no change-caused
failure may be skipped (measured: zero missed failures); NFR-3 scalability and
portability — no third-party dependency, one SQLite store, Python 3.12+.

**Evidence we already have.** Across 12 verified mutations on four targets
(three generated projects plus the tool's own suite), the tool skipped 69–85 % of
the suite depending on policy while detecting every change-caused failure
(worst-case recall 1.000), raised the fault-detection order from APFD 0.659 to
0.925, and saved 63–85 % of test execution time; the tool itself is covered by 99
automated tests.

**Process and deliverables.** Scrum with three four-week sprints and weekly
evidence in the GitHub repository; deliverables are the tool, the repository, the
final report (IEEE TSE format) and an offline presentation with a live demo.

Non-goals: we are not writing a test generator, not building a server/CI product,
and not training a machine-learning model.

Could you please confirm that this topic is acceptable, or let us know any concern
we should address before we start?

Thank you very much.

Best regards,

Zhao Zun 赵尊, Team leader (GitHub: @bufuzhouyu)

---

## 中文对照（自己看，不必发给 TA）

**题目：** 面向 pytest 的风险感知测试选择、排序与闪烁测试排查工具

**问题：** 开发者只改了一小块代码，目前唯一安全的做法是把整个测试套件全跑一遍，于是反馈时间取决于测试总量而不是改动大小；而随便跳过测试更糟——漏掉的回归会被报成"绿色通过"。

**基座与原创点：** 基于开源项目 **pytest**（使用其插件接口，不改它的源码），我们实现自己的算法：(1) 用 PEP 669 `sys.monitoring` 观察"每个测试执行了哪些文件"，并设计了延迟的按代码对象行级插桩；(2) 把"观察到的执行记录 + 静态导入闭包 + 历史结果 + 闪烁信号"融合成三档可审计的策略（fast / balanced / safe）；(3) 可解释的风险排序；(4) 差分式闪烁判定。

**安全设计：** 无依赖记录、上次失败、被判闪烁、以及显式标记 `@pytest.mark.risktest_always` 的测试无条件执行；止损规则限制最大跳过比例；构建/测试配置变更则强制全量运行。

**非功能需求：** 性能（file 粒度观测开销 < 20%，实测 −8.5%…+16.7%）、可靠性（不得漏掉任何由改动引起的失败，实测 0 漏检）、可扩展与可移植（无第三方依赖、单个 SQLite 存储、Python 3.12+）。

**已有证据：** 4 个实验对象、12 个已确认能弄坏测试的缺陷，三种策略共 36 次运行：跳过 69%–85%，真实失败全部命中（最差召回 1.000），失败暴露顺序 APFD 从 0.659 提升到 0.925，节省 63%–85% 的测试执行时间；工具自身有 99 个自动化测试。

**过程与交付：** Scrum 三个四周迭代，仓库每周留证；交付物是工具、仓库、IEEE TSE 格式结题报告，以及线下汇报与现场演示。

**明确不做：** 不是测试生成器、不做服务器/CI 产品、不训练机器学习模型。

