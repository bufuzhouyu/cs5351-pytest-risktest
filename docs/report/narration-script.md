# 汇报录屏旁白稿（7 分钟）

适用文件：`docs/report/presentation.pptx` + `scripts/demo.ps1`

## 录制前 5 分钟检查

1. 运行一次 `.\scripts\demo.ps1 -NoPause`，确认最后出现 `2 failed` 和报告表格。正式录屏时不要加 `-NoPause`，每一步会停下来等你按回车。
2. 关闭微信、QQ、浏览器个人页面和邮箱通知。任务栏只保留终端、PowerPoint 和资源管理器。
3. 终端字号调到 18 到 20，窗口宽度约 1400 像素。PPT 用 16:9，全屏播放。
4. 录音设备先用 10 秒测试，确认没有回声。建议 1080p、30 帧。
5. 演示使用临时目录，仓库文件不会被改动。结束后可以直接关闭终端。

时间轴：0:00 封面，0:25 问题，1:05 约束，1:40 开源基座，2:15 架构与策略，3:05 现场演示，5:05 评测协议，5:35 结果，6:15 局限，6:40 过程与结尾。

---

## 0:00–0:25 封面

幻灯片：`Risk-aware test selection for pytest`

旁白：

大家好，我们做的是 CS5351 的软件工程工具项目，名字是 pytest-risktest。它解决一个每天都会遇到的问题：改了几行代码，到底需要重跑哪些测试。我们的目标不是单纯少跑测试，而是在少跑的同时，不让任何一个真实失败被跳过。

---

## 0:25–1:05 问题

幻灯片：`Feedback time follows suite size, not change size`

旁白：

先看基线。我们在 12 次已经确认会破坏测试的改动上测量，一次改动真正影响到的测试只占整个套件的 9% 到 31%。但默认做法是把 100% 的测试全部跑一遍，所以反馈时间跟着套件规模增长，而不是跟着改动规模增长。

更麻烦的是，随便跳过测试会把真实失败藏起来。一次漏报就会让红色提交看起来是绿色，这比慢更严重。

---

## 1:05–1:40 四个约束

幻灯片：`Four constraints shape the selection problem`

旁白：

这四个约束决定了设计。第一，证据不完整：第一次运行、过期的依赖记录、子进程里的测试，都没有可靠的依赖数据。第二，观测本身不能太贵，我们把文件级观测开销限制在 20% 以内。第三，每个被跳过的测试都要有可复查的理由。第四，安全优先，漏掉一个失败就说明这个工具不该被使用。

---

## 1:40–2:15 开源基座与相关工作

幻灯片：`pytest supplies the extension points and the ground truth`

旁白：

我们基于开源项目 pytest 做插件，因为它有稳定的 pytest11 插件入口，能在收集、运行和报告三个阶段接入，而且每个测试的通过与耗时本身就是评测的真值，不需要人工标注。

相关工作主要有三类：构建系统里的测试影响分析、工业界的预测式测试选择，以及 pytest-testmon 这类基于覆盖率的工具。我们保留它们的核心思想，补上两个缺口：可解释的决策，以及明确的安全边界。

---

## 2:15–3:05 架构与策略

幻灯片：`Test execution becomes selection evidence`，然后快速切到 `Policies expose the precision and cost trade-off`

旁白：

工具分四步。PEP 669 监控器记录每个测试实际执行了哪些文件；静态导入图补上“可能到达”的文件；两者和历史结果一起存进一个 SQLite 文件；选择引擎据此生成计划，按风险排序后交给 pytest。

策略是显式的。fast 只看动态证据，跳过大约 85%；balanced 再看一跳导入关系，跳过 71%；safe 使用完整闭包，跳过 69%，推荐作为 CI 门禁。

安全层有三条：新测试、上次失败和闪烁测试必跑；最多只允许跳过 90%；无法追踪的测试可以用 risktest_always 标记强制运行。

---

## 3:05–5:05 现场演示

画面：切到终端，运行 `.\scripts\demo.ps1`。按回车推进每一步。

### 3:05–3:35 预热

操作：脚本生成一个 88 个测试的示例工程。

旁白：

演示用一个临时工程，不会改动仓库。第一步是全量预热。这时 88 个测试全部运行，工具记录每个测试真正执行过的文件，作为下一次选择的证据。

### 3:35–3:55 制造回归

操作：脚本修改 `feature_02.py` 里的权重。

旁白：

现在制造一个真实回归：把 feature_02 的权重从 3 改成 1。两个依赖这个模块的测试会失败。

### 3:55–4:25 先看计划

操作：执行 `impact`

旁白：

先不跑测试，直接看计划。工具只选中 8 个测试，跳过 91%。每个测试都给出理由：7 个直接执行了改动文件，1 个来自导入闭包。改动文件和选择依据都能在报告里复查。

### 4:25–4:55 选择性运行

操作：执行 safe 策略

旁白：

现在真正运行。8 个测试里有两个失败。注意，这两个失败被明确报告出来，没有被跳过，也没有被误判成闪烁测试。这就是我们要保证的安全性：省时间，但不牺牲真值。

### 4:55–5:05 报告

操作：脚本打印 Markdown 报告

旁白：

运行结束后会同时生成 JSON、Markdown 和 HTML 报告，包含改动文件、选择原因和失败列表，CI 可以直接读取 JSON。

---

## 5:05–5:35 评测协议

幻灯片：`The evaluation contract was frozen before measurement`

旁白：

评测协议在看结果之前就固定了。四个目标：三个生成的 layered 工程，加上本项目自己的测试套件。每次注入的缺陷都必须先证明能打挂至少一个测试，真值来自不带插件的普通 pytest 运行。每个策略开始前都恢复依赖库快照，避免后一个策略看到已经被消费掉的改动。

---

## 5:35–6:15 结果

幻灯片：`Every verified failure was detected with 69% to 85% of the suite skipped`

旁白：

36 次运行的结果是这样：fast 跳过 85.4%，balanced 跳过 71.4%，safe 跳过 69.3%，三个策略的最差召回率都是 1.000，漏掉的失败是 0。

排序也有效。全量运行按收集顺序的 APFD 是 0.659，按风险排序后是 0.925，失败更早出现。测试执行时间节省了 63% 到 85%。需要说明的是，纯墙钟时间只节省 10% 到 18%，因为小套件里解释器和 pytest 启动占了固定成本。

---

## 6:15–6:40 局限

幻灯片：`Two measured limits shaped the design`

旁白：

两个局限我们也做了测量。第一，行级粒度在 CPU 密集的套件上会慢 5 倍以上，所以在项目自己的套件上是 26%，我们仍然把文件级设为默认。第二，子进程里的代码追踪不到。实验里不声明时，两个真实失败漏掉一个；加上 risktest_always 后两个都能检出。

另外，同长度、同一秒内的改动可能让 Python 复用旧字节码。测试和评测脚本现在都会清理缓存，这也是我们写进风险登记的一个真实教训。

---

## 6:40–7:00 过程与结尾

幻灯片：`Three sprints produced a tool, an evaluation and a reviewable process`

旁白：

三个 sprint 分别完成工具骨架和安全网、排序和闪烁测试排查、端到端测试和评测。现在仓库里有 99 个自动化测试、Windows 和 Ubuntu 的 CI，以及冻结的评测契约。我们还发现并修复了两个会破坏评测可信度的问题，都记录在风险登记里。

下一步是接入第三方项目、支持多行缺陷，并为长期被跳过的测试补充依赖刷新策略。谢谢，接下来是提问。

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

## 录屏时不要做的事

- 不要展示个人文件、聊天窗口或浏览器标签。
- 不要现场修改仓库源码，演示只在临时目录进行。
- 不要讲还没实现的功能，未来工作放在最后一句。
- 不要为了赶时间跳过失败的演示步骤，安全失败检出正是重点。