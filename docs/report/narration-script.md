# 线下汇报讲稿（7 分钟）

适用文件：`docs/report/presentation.pptx` + `scripts/demo.ps1`

团队：赵尊（组长）、代佳乐、肖宇、张力元、庄志洋、周浩然。
汇报形式：线下，PPT 投屏 + 笔记本现场演示，不录视频。

## 上台前 10 分钟检查

1. 用汇报电脑打开 PPT，切到放映模式，确认投影比例和分辨率。
2. 在仓库根目录打开终端，字号调到 18 到 20，背景浅色。
3. 先跑一次 `.\scripts\demo.ps1 -NoPause` 预热机器，确认最后出现 `2 failed`，然后关闭。
4. 打开 `docs/report/figures/` 作为备用截图，万一终端出问题可以接着讲。
5. 关闭微信、QQ、邮箱和浏览器个人页面，手机静音。
6. 把讲稿按下面的时间点折角，方便抬眼。

时间轴：0:00 开场，0:35 问题，1:15 方案，2:15 现场演示，4:45 评测，5:50 过程，6:35 收尾。

---

## 0:00–0:35 开场

幻灯片：`Risk-aware test selection for pytest`

旁白：

大家好，我们是第六组，项目是 pytest-risktest。我们解决一个每天都会遇到的问题：改了几行代码，到底需要重跑哪些测试。我们的目标不只是少跑测试，而是在少跑的同时，不让任何一个真实失败被忽略。

---

## 0:35–1:15 问题与约束

幻灯片：`Feedback time follows suite size, not change size`，然后 `Four constraints shape the selection problem`

旁白：

我们在 12 次已经确认会破坏测试的改动上测量，一次改动真正影响到的测试只占整个套件的 9% 到 31%，但默认做法是把 100% 全部跑一遍，所以反馈时间跟着套件规模增长。

更麻烦的是，随便跳过测试会把真实失败藏起来。一次漏报就会让红色提交看起来是绿色。因此设计受到四个约束：证据可能不完整、观测本身不能太贵、每个跳过都要能复查、以及安全优先。

---

## 1:15–2:15 方案

幻灯片：`pytest as the extension point and ground truth`，然后 `Test execution becomes selection evidence` 和 `Policies expose the precision and cost trade-off`

旁白：

我们基于开源项目 pytest 做插件，因为它有稳定的插件入口，而且每个测试的通过与耗时本身就是评测真值。

工具分四步：PEP 669 监控器记录每个测试实际执行了哪些文件；静态导入图补上可能到达的文件；两者和历史结果一起存进一个 SQLite 文件；选择引擎生成计划，按风险排序后交给 pytest。

策略有三档：fast 只看动态证据，跳过约 85%；balanced 再看一跳导入关系，跳过约 71%；safe 使用完整闭包，跳过约 69%，推荐用于 CI。安全层有三条：新测试、上次失败和闪烁测试必跑；最多只跳过 90%；无法追踪的测试用 risktest_always 强制运行。

---

## 2:15–4:45 现场演示

操作：切到终端，运行 `.\scripts\demo.ps1`。每讲完一步按一次回车。

### 2:15–2:40 预热

旁白：

演示用一个临时工程，不会改动仓库。第一步是全量预热：88 个测试全部运行，工具记录每个测试真正执行过的文件，作为下一次选择的证据。

### 2:40–3:00 制造回归

旁白：

现在制造一个真实回归：把 feature_02 的权重从 3 改成 1。两个依赖这个模块的测试会失败。

### 3:00–3:30 先看计划

旁白：

先不跑测试，直接看计划。工具只选中 8 个测试，跳过 91%。每个测试都给出理由：7 个直接执行了改动文件，1 个来自导入闭包。改动文件和选择依据都能在报告里复查。

### 3:30–4:05 选择性运行

旁白：

现在真正运行。8 个测试里有两个失败。注意，这两个失败被明确报告出来，没有被跳过，也没有被误判成闪烁测试。这就是我们要保证的安全性：省时间，但不牺牲真值。

### 4:05–4:45 报告与兜底

旁白：

运行结束后会同时生成 JSON、Markdown 和 HTML 报告，包含改动文件、选择原因和失败列表，CI 可以直接读取 JSON。

如果现场终端出问题，就切到备用截图，按同样的顺序讲完五步。

---

## 4:45–5:50 评测

幻灯片：`Evaluation contract frozen before measurement`，然后 `69% to 85% skipped, every failure detected`

旁白：

评测协议在看结果之前就固定了。四个目标：三个生成的 layered 工程，加上本项目自己的测试套件。每次注入的缺陷都必须先证明能打挂至少一个测试，真值来自不带插件的普通 pytest 运行。每个策略开始前都恢复依赖库快照。

36 次运行的结果：fast 跳过 85.4%，balanced 跳过 71.4%，safe 跳过 69.3%，三个策略的最差召回率都是 1.000，漏掉的失败是 0。全量运行按收集顺序的 APFD 是 0.659，按风险排序后是 0.925，失败更早出现。测试执行时间节省了 63% 到 85%。纯墙钟时间只节省 10% 到 18%，因为小套件里解释器和 pytest 启动占了固定成本。

---

## 5:50–6:35 局限与过程

幻灯片：`Two measured limits shaped the design`，然后 `Three sprints, one reviewable process`

旁白：

两个局限也做了测量。第一，行级粒度在 CPU 密集的套件上会慢 5 倍以上，所以项目自己的套件是 26%，我们仍然把文件级设为默认。第二，子进程里的代码追踪不到。不声明时两个真实失败漏掉一个，加上 risktest_always 后两个都能检出。

过程上，三个 sprint 分别完成工具骨架和安全网、排序和闪烁测试排查、端到端测试和评测。仓库里有 99 个自动化测试、Windows 和 Ubuntu 的 CI，以及冻结的评测契约。我们还发现并修复了两个会破坏评测可信度的问题，都记录在风险登记里。

团队六个人分别负责仓库与发布、测试、文档、评测、汇报和报告，每个人的工作都通过 Issue 和 Pull Request 留痕。

---

## 6:35–7:00 收尾

旁白：

下一步是接入第三方项目、支持多行缺陷，并为长期被跳过的测试补充依赖刷新策略。以上是我们的汇报，谢谢大家，欢迎提问。现场演示的终端我会保留着，如果需要可以再跑一次。

---

## 附：如需英文汇报

每页可用一句话起头：

1. We built pytest-risktest, a tool that runs the tests a change can affect without hiding failures.
2. A verified change affected 9% to 31% of the suite, while the default workflow runs 100%.
3. Four constraints drove the design: incomplete evidence, observation cost, reviewability and safety.
4. pytest gives us the plug-in API and the ground truth; our contribution is explainable selection with a safety budget.
5. The tool turns observed execution, static reachability and history into a reviewable plan.
6. Three named policies make the precision and cost trade-off explicit.
7. The evaluation contract was frozen before measurement.
8. Across 36 verified mutations, every failure was detected with 69% to 85% of the suite skipped.
9. We measured two limits and changed the defaults because of them.
10. Three sprints produced a working tool, a reproducible evaluation and a reviewable process.

## 现场汇报注意

- 不要展示个人文件、聊天窗口或浏览器标签。
- 不要现场修改仓库源码，演示只在临时目录进行。
- 不要讲还没实现的功能，未来工作放在最后一句。
- 终端一旦卡住，不要反复敲命令，直接切备用截图。
- 控制时间：讲到 4:45 必须结束演示，否则后面的结果没有时间讲。
