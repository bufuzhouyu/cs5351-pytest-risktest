# GitHub 零基础教程（6 人团队版）

这份教程假设你**从没使用过 GitHub**。全程用 GitHub Desktop 的图形界面，不需要背命令。队长先做第一部分，然后五个成员照第二部分做。

> 界面语言：GitHub Desktop 官方只有英文。按钮的中英文对照见 `docs/12-github-desktop-english-cheatsheet.md`，照着点即可。

先理解三个东西：

- **本地文件**：`D:\课程\CS5351_Software-Engineering\project` 这个文件夹。
- **本地仓库**：文件夹里的 `.git`，记录每次修改的历史。
- **GitHub 远程仓库**：网页上的副本，团队成员通过它同步代码。

提交（commit）是"拍一张本地快照"，推送（push）是"把快照上传到 GitHub"。

## 当前仓库状态（2026-11-21）

- 六位成员、学号、GitHub 用户名和分工已写入 `TEAM.md` 和报告。
- 最终考核改为线下 Pre，不再录制视频；M5 负责 PPT、现场演示和彩排。
- 换行符已统一：文本文件用 LF，三个 PowerShell 脚本用 CRLF，PPT/图片按二进制处理。
- 队长已经完成一次提交 `cc21433`（`bufuzhouyu` 账号）。剩下的改动在 Desktop 里提交后 Push 即可。

---

## 第一部分：队长 30 分钟

如果仓库已经 Publish（当前就是这个状态），第 1–3 步不用重做，直接从第 4 步开始。第 1–3 步只在第一次建仓库时做一次。

### 1. 注册 GitHub

1. 打开 https://github.com/signup
2. 用学校邮箱注册，完成邮箱验证。
3. 用户名建议用真实姓名拼音，例如 `zhangsan-cs5351`。
4. 记下用户名和邮箱，后面配置要用。

### 2. 安装 GitHub Desktop

1. 打开 https://desktop.github.com/download/
2. 下载 Windows 版，双击安装。
3. 打开后选择 **Sign in to GitHub.com**，在浏览器里登录并授权。

### 3. 把本地项目加入 GitHub Desktop

1. 菜单 **File → Add local repository**。
2. 选择 `D:\课程\CS5351_Software-Engineering\project`。
3. 点 **Add repository**。
4. 左侧出现 **Changes**，说明它识别到了本地仓库。

### 4. 提交当前改动

在 GitHub Desktop 左侧点 **Changes**，确认列表里包含这些文件（如果某次提交已经包含过，就不会再出现）：

- `.gitattributes`
- `TEAM.md`
- `README.md`、`README.zh-CN.md`
- `docs/09-topic-introduction-for-ta.md`
- `docs/10-github-team-workflow.md`、`docs/11-github-desktop-beginner-guide.md`、`docs/12-github-desktop-english-cheatsheet.md`
- `docs/process/two-week-plan.md`
- `docs/report/presentation.pptx`、`narration-script.md`、`presentation-outline.md`
- `scripts/check-team-records.ps1`

**不要勾选** `out/`、`.risktest/`、`.pytest_cache/`、`__pycache__/`。这些是生成文件，已经被 `.gitignore` 忽略。

在左下角填写：

- **Summary**：`chore: normalize line endings and finalize offline presentation`
- **Description**：`Adds .gitattributes, team member details, the offline presentation script and the updated deck cover.`

点 **Commit to main**。

如果这是你第一次建仓库，Summary 改成 `chore: add team roster and two-week plan` 也可以。提交说明只要能让别人看懂这次改了什么就行。

### 5. 发布到 GitHub

如果仓库还没发布：顶部会出现 **Publish repository**，点击。

如果仓库已经发布过：顶部会显示 **Push origin**，点它即可。

首次发布按下面做：

1. 点 **Publish repository**。
2. **Name** 填 `cs5351-pytest-risktest`。
3. 如果课程要求公开就取消勾选 **Keep this code private**，否则保持私有。
4. 点 **Publish repository**。
5. 完成后打开 https://github.com ，在 **Your repositories** 里能看到它。

### 6. 邀请另外 5 人

1. 打开仓库网页 → **Settings**。
2. 左侧 **Collaborators** → **Add people**。
3. 输入 5 位同学的 GitHub 用户名，逐个邀请。
4. 同学在邮箱里接受邀请。
5. 如果仓库是私有的，把 TA 和老师也加进来（或按课程要求设为公开）。

### 7. 保护 main 分支（防止直接改主分支）

仓库网页 → **Settings → Branches → Add branch protection rule**：

- Branch name pattern：`main`
- 勾选 **Require a pull request before merging**
- **Require approvals** 设为 1
- 勾选 **Require status checks to pass before merging**，选择 CI
- 保存

这样每个人都要走"开分支 → 提 PR → 别人审核 → 合并"的流程。

### 8. 换行符提示（LF/CRLF）

如果 Desktop 提示 *This file uses 'LF' line endings, but Git is configured to convert them to 'CRLF'*，这不是错误。

它的意思是：文件现在用 LF，Windows 的 Git 想把检出后的文件改成 CRLF。两个人分别用 Windows 和 Linux 时，这种转换会让同一个文件显示成"整份都改了"，所以我们在仓库里统一了规则：

- 新增 `.gitattributes`：所有文本文件用 LF；
- `*.ps1`、`*.bat`、`*.cmd` 用 CRLF；
- `*.pptx`、`*.xlsx`、图片按二进制，不做任何转换；
- 仓库本地设置 `core.autocrlf=false`，不再自动转换。

正常提交即可，不会影响代码。**不要点 Discard changes**，那会丢掉你还没提交的修改。也不要安装第三方"换行符修复工具"。

如果提示再次出现，先关掉 Desktop 再打开。仍然出现就把提示发到群里，不要自己乱改全局 Git 设置。

---

## 第二部分：每位成员 10 分钟

### 1. 准备工作

1. 注册 GitHub 账号并接受邀请。
2. 安装 GitHub Desktop，登录自己的账号。
3. **File → Clone repository**，在列表里找到 `cs5351-pytest-risktest`，选择本地保存位置，点 **Clone**。

### 2. 第一次练习：写自己的简介

1. 在 GitHub Desktop 顶部点 **Current branch → New branch**。
2. 分支名：`sprint-3/intro-你的名字拼音`。
3. 用 VS Code 或记事本新建 `docs/team/你的名字拼音.md`，写：

```markdown
# 姓名（学号）

- GitHub：@你的用户名
- 专业/年级：
- 技术背景：
- 在本项目中的任务：
- 感兴趣的方向：
```

4. 回到 GitHub Desktop，左侧会显示这个新文件。
5. 左下角 Summary 填 `docs: add personal introduction for <姓名>`，点 **Commit to branch**。
6. 顶部点 **Publish branch**。
7. 点 **Create Pull Request**，浏览器会打开 PR 页面，点 **Create pull request**。

### 3. 找一位同学审核并合并

1. 在 PR 页面右侧 **Reviewers** 选择一位同学。
2. 对方打开 **Files changed → Review changes → Approve → Submit review**。
3. 你点 **Merge pull request → Confirm merge**。
4. 回到 GitHub Desktop，点 **Fetch origin**，再点 **Pull origin**，把合并后的内容同步到本地。

这一步完成后，你的 GitHub 头像就会出现在 **Insights → Contributors** 里。

### 4. 做正式任务

看完 `docs/process/two-week-plan.md` 里分配给你的任务后，重复上面的流程：

1. **Current branch → New branch**，例如 `sprint-3/us-21-你的名字`。
2. 修改文件，写一个小而完整的改动。
3. Commit（Summary 写清楚做了什么，例如 `US-21: add selector edge-case tests`）。
4. Publish branch。
5. Create Pull Request，写 `Closes #21`。
6. 找同学 review，合并。

不要直接在 `main` 上改，也不要一次提交几十个文件。

---

## 第三部分：6 个任务（复制到 Issue 里）

在仓库网页 **Issues → New issue**，每个任务建一个 issue，指派给对应成员。

1. **M1 队长**：`chore: repository setup, branch protection and release v0.1.0`
   验收：CI 绿色、main 受保护、打 tag `v0.1.0`。

2. **M2 测试**：`test: add 10 regression tests for selector, CLI and reporting`
   验收：新增测试通过，PR 里附上测试数量和覆盖情况。

3. **M3 文档**：`docs: Chinese README and troubleshooting guide`
   验收：`README.zh-CN.md` 与英文 README 同步，所有链接可点。

4. **M4 评测**：`eval: re-run benchmark with four subjects and four mutations`
   验收：更新 `benchmark/results/summary.md` 和图表，并写一段结果解释。

5. **M5 汇报**：`presentation: final deck and seven-minute offline live demo`
   验收：现场讲解与演示合计不超过 7 分钟，彩排计时和备用截图记录在 PR 里。

6. **M6 报告**：`report: IEEE TSE formatting, bios and contribution table`
   验收：报告含 6 人简介、self-reflection、贡献表和全部图表。

---

## 第四部分：每天怎么用

- **开始工作前**：GitHub Desktop 点 **Fetch origin → Pull origin**。
- **做完一小步**：Commit 一次，Summary 用一句话说清楚。
- **完成一个任务**：Push → PR → 找人 review → 合并。
- **每周日**：更新 `docs/process/weekly-evidence.md`，写清本周谁做了什么、对应哪个 Issue/PR。
- **提交前**：确认 Changes 里没有 `out/`、`.risktest/`、`.pytest_cache/`、`__pycache__/`；确认没有 LF/CRLF 提示。
- **提交前检查**：

```powershell
.\scripts\check-team-records.ps1 -Members "姓名1","姓名2","姓名3","姓名4","姓名5","姓名6"
```

---

## 第五部分：常见问题

**Q：GitHub Desktop 显示 "No local changes"，但我改了文件？**
确认你改的是 `Clone` 下来的那个文件夹，不是桌面上的旧副本。

**Q：Desktop 提示 "This file uses 'LF' line endings..." 怎么办？**
这不是错误，见第一部分第 8 节。仓库已经用 `.gitattributes` 统一了换行符：文本用 LF，PowerShell 脚本用 CRLF，PPT 和图片按二进制处理。直接正常提交即可，不要点 **Discard changes**，也不要安装第三方换行符修复工具。如果重启 Desktop 后仍然出现，把提示发到群里。

**Q：Push 失败，提示 rejected？**
别人先合并了新内容。点 **Fetch origin → Pull origin**，解决冲突后再 push。第一次遇到冲突就找队长一起看，不要强推。

**Q：提交作者不是我？**
GitHub Desktop 用登录账号提交。检查 **File → Options → Git** 里的 Name/Email，或在仓库目录执行：

```powershell
git config user.name "你的名字"
git config user.email "你的GitHub邮箱"
```

**Q：老师说看不到仓库？**
私有仓库必须在 Settings → Collaborators 里邀请老师；或者按课程要求改为 public。

**Q：PR 里显示很多无关文件？**
你的分支是从旧版本切的，或者把临时文件加进来了。先 Pull main，再重新建分支；`out/`、`.risktest/`、`__pycache__/` 不要提交。

**Q：能不能让队友代我提交，显得我有记录？**
不要。课程看的是真实贡献，伪造提交很容易被识别（没有 review、改动无意义、时间集中）。没做完就在周三例会上说明，调整分工。
