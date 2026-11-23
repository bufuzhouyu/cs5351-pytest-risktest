# Troubleshooting

以下命令在仓库根目录的 PowerShell 中运行。完整运行方式见[英文 README](../README.md)和[中文 README](../README.zh-CN.md)。

## 1. Python is older than 3.12

**症状**：插件提示监控不可用，或缺少 `sys.monitoring`。

**检查**：运行 `python -V` 和 `python -c "import sys; print(sys.executable); print(hasattr(sys, 'monitoring'))"`。

**解决**：切换到 Python 3.12 或更高版本，重建项目虚拟环境并重新安装依赖。监控属性应显示 `True`。

## 2. pytest is not installed

**症状**：出现 `No module named pytest`。

**检查**：运行 `python -m pytest --version`。

**解决**：在当前虚拟环境运行 `python -m pip install -e ".[dev]"`，再检查版本。运行测试时继续用同一解释器。

## 3. The plug-in is not loaded

**症状**：pytest 报 `unrecognized arguments: --risktest`。

**检查**：运行 `python -m pytest --help | Select-String risktest`，确认帮助中有 RiskTest 选项。

**解决**：已安装项目时，确认 pytest 与项目安装在同一环境，并检查是否禁用了插件自动加载。从源码运行时，先设置 `$env:PYTHONPATH = "src"`，再运行 `python -m pytest -p pytest_risktest.plugin --help | Select-String risktest` 显式加载并复查。

## 4. No dependency traces after the first run

**症状**：首次运行后，状态仍显示没有测试依赖记录。

**检查**：已安装项目时运行 `risktest status`。从源码运行时先设置 `$env:PYTHONPATH = "src"`，再执行 `python -m pytest_risktest.cli status`。

**解决**：在同一仓库根目录和 Python 环境中运行首次采集命令，再查状态，确认有测试记录和依赖边。

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -p pytest_risktest.plugin --risktest --risktest-policy=off
python -m pytest_risktest.cli status
```

## 5. A change in a subprocess test is not detected

**症状**：文件主要由测试启动的子进程执行，对应测试未被选中。

**检查**：查看测试是否启动子进程，并用 `python -m pytest --markers | Select-String risktest_always` 检查标记。源码运行时加 `-p pytest_risktest.plugin`。

**解决**：由测试维护者给对应函数加 `@pytest.mark.risktest_always`（模块需导入 `pytest`），使测试始终运行。重跑选择流程核对该用例；标记本身不会补录子进程依赖。

## 6. LF/CRLF warning in GitHub Desktop

**症状**：Git 提示 LF 与 CRLF 转换，或差异中出现整文件换行变动。

**检查**：运行 `git check-attr text eol -- README.zh-CN.md docs/13-troubleshooting.md`、`git config --show-origin --get core.autocrlf` 和 `git diff --check`。

**解决**：按仓库 `.gitattributes` 的规则保存文件。若团队要求关闭本仓库的隐式转换，执行 `git config --local core.autocrlf false`。显式的 `eol` 规则仍适用。复查文件差异。

## 7. CI fails only on Windows

**症状**：Windows 作业失败，其他平台通过。

**检查**：从 PR 的 Checks 打开 Windows 日志，定位第一个失败步骤，并用 `python -V`、`python -m pytest --version` 对照运行环境。

**解决**：用相同的 Shell、工作目录及命令复现，检查路径、引号、换行和依赖。将失败日志和复现输出交给对应维护者。

## 8. Report or cache files appear in git status

**症状**：报告或缓存目录出现在改动列表。

**检查**：运行 `git status --short`、`git check-ignore -v -- out/ .risktest/ .pytest_cache/ __pycache__/` 和 `git diff --cached --name-only`。

**解决**：只暂存本次文档。误暂存文件时，用 `git restore --staged -- <实际文件路径>` 取消暂存并保留本地文件。若生成物已被跟踪，记录路径并通知维护者。
