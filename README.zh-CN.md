# pytest-risktest

**面向 pytest 的风险感知测试选择、优先级排序与不稳定测试（flaky）分类。**

`pytest-risktest` 是一个面向开发团队的软件工程工具：它会观察每个测试实际覆盖了项目的哪些文件，然后依据这些证据，*只运行受本次改动影响的测试*，并按*风险顺序*执行，同时拒绝用自身的跳过决策来掩盖失败。

本仓库是 CS5351 软件工程课程项目（团队 `<team name>`，项目 `pytest-risktest`）。团队成员为赵尊（组长，`@bufuzhouyu`）、代佳乐（`@lele2204`）、肖宇（`@kaito-hqs`）、张力元（`@Yuan07292003`）、庄志洋（`@f-zhuang`）和周浩然（`@Cyanova-zhou`）。课程要求与本仓库产物的对应关系见
[docs/00-assignment-mapping.md](docs/00-assignment-mapping.md)。

## 功能概览

| 能力 | 说明 |
| --- | --- |
| 测试选择（TIA） | 将*观测到的*每个测试的依赖（基于 PEP 669 监控）与*静态*导入闭包融合，并受可审计策略（`fast`、`balanced`、`safe`）约束。 |
| 优先级排序 | 按风险对选中的测试排序（近期失败、已知 flaky 情况、测试覆盖改动代码的比例），以提升 APFD。 |
| Flaky 分类 | 差分 flaky 检测（依赖指纹相同但结果不同）加顺序扰动重跑（`risktest flaky-check`）。 |
| 安全护栏 | 最大跳过率止损规则；对未见过/失败/不稳定的测试设“始终运行”集合；为跨越进程边界的测试提供 `@pytest.mark.risktest_always` 逃生通道。 |
| 证据 | JSON/Markdown/HTML 运行报告、SQLite 依赖存储、带冻结指标契约的基准测试框架。 |

## 安装与运行

该工具**没有第三方运行时依赖**（需要 Python 3.12+，因为用到 `sys.monitoring`）。

```powershell
# 在仓库根目录，无需安装任何东西
$env:PYTHONPATH = "src"

# 1) 预热运行：记录依赖追踪信息，执行全部测试
python -m pytest tests -p pytest_risktest.plugin --risktest --risktest-policy=off

# 2) 改动之后：只运行受影响的测试，按风险顺序
python -m pytest tests -p pytest_risktest.plugin --risktest --risktest-policy=safe
```

作为包安装后，插件会自动加载：

```powershell
pip install -e .
pytest --risktest --risktest-policy=safe
```

### 命令行

```powershell
risktest status                     # 该工具对本仓库已知的信息
risktest impact --policy safe       # 试运行：一次改动会触发哪些测试？
risktest flaky-check -- pytest -q   # 顺序扰动重跑，标记出 flaky 测试
risktest report --report .risktest/last-run.json
risktest clean --yes                # 删除本地状态
```

### 主要选项

| 选项 | 含义 |
| --- | --- |
| `--risktest-policy={off,fast,balanced,safe}` | 选择影响闭包的多少部分（`off` = 仅追踪，`safe` = CI 推荐值） |
| `--risktest-granularity={file,line}` | 依赖粒度；实测默认值为 `file` |
| `--risktest-line-strategy={local,global}` | 按代码对象（默认）或解释器级别的行事件 |
| `--risktest-order={risk,original,shuffle}` | 所选测试的排序方式 |
| `--risktest-changed={auto,hash,git,none}` | 改动检测方式（无 git 也能工作） |
| `--risktest-max-deselect=90` | 止损规则：取消选择的测试占比不得超过该值 |
| `--risktest-trace-only` | 记录追踪信息但仍运行全部测试 |

## 实测结果

所有数字均来自 `benchmark/run_bench.py`，它向四个目标注入*经校验的*变异（即能证明至少使一个测试失败的变异）：三个生成的分层项目以及本项目自身（自举）。完整细节见
[benchmark/results/summary.md](benchmark/results/summary.md)。

| 策略 | 运行次数 | 跳过率 | 召回率（最差） | 漏检失败数 | APFD（工具） | APFD（基线） | 节省的工作量 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 12 | 0.854 | 1.000 | 0 | 0.925 | 0.659 | 0.851 |
| balanced | 12 | 0.714 | 1.000 | 0 | 0.925 | 0.659 | 0.656 |
| safe | 12 | 0.693 | 1.000 | 0 | 0.925 | 0.659 | 0.634 |

* *节省的工作量*不计解释器启动开销，仅使用单个测试的耗时统计。
* 观测开销：本项目测试套件下文件粒度为约 0–17 %，行粒度为 26 %；在 CPU 密集型的生成测试套件上则超过 500 %
  （[benchmark/results/tracing-strategies.md](benchmark/results/tracing-strategies.md)）。
* 一项边界实验展示了该方法无法覆盖的情形以及所设计的缓解措施：
  [benchmark/results/untraced-paths.md](benchmark/results/untraced-paths.md)。

## 仓库结构

```
src/pytest_risktest/   插件、监控器（PEP 669）、依赖图、存储、选择器、flaky、指标、报告、CLI
tests/                 96 个测试：单元测试，以及在子进程中运行的插件端到端测试
benchmark/             被测对象生成器、变异算子、测试框架、实验、结果
scripts/               开发辅助脚本、燃尽图、存储检查器、依赖图导出器
docs/                  作业对应关系、问题陈述、需求、架构、过程、报告草稿
.github/               issue 与 pull request 模板、CI 工作流
```

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/00-assignment-mapping.md](docs/00-assignment-mapping.md) | 每一条课程要求 → 在何处得到满足 |
| [docs/01-problem-statement.md](docs/01-problem-statement.md) | 有边界的问题陈述与非目标 |
| [docs/02-open-source-base-and-related-work.md](docs/02-open-source-base-and-related-work.md) | 开源基座选择与相关工作 |
| [docs/03-requirements.md](docs/03-requirements.md) | 用户故事、验收标准、非功能性需求 |
| [docs/04-architecture.md](docs/04-architecture.md) | 组件与带实测数据的架构决策记录 |
| [docs/05-evaluation-contract.md](docs/05-evaluation-contract.md) | 冻结的指标、阈值与测试用例 |
| [docs/06-risk-register.md](docs/06-risk-register.md) | 风险登记册与止损规则 |
| [docs/07-coding-agent-contract.md](docs/07-coding-agent-contract.md) | 编码智能体的使用与评审方式 |
| [docs/08-trace-requirement-to-result.md](docs/08-trace-requirement-to-result.md) | 需求 → 代码 → 测试 → 证据 的追溯矩阵 |
| [docs/process/](docs/process/) | 迭代计划、每周证据、燃尽图 |
| [docs/report/report-draft.md](docs/report/report-draft.md) | 按 IEEE TSE 结构撰写的终期报告草稿 |

## 开发

```powershell
.\scripts\dev.ps1              # 单元测试 + 集成测试
.\scripts\dev.ps1 -Benchmark   # 复现评估结果
```

## 许可证

MIT，见 [LICENSE](LICENSE)。
