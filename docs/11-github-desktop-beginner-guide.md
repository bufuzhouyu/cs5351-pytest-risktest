# GitHub 零基础教程（6 人团队版）

这份教程假设你**从没使用过 GitHub**。全程用 GitHub Desktop 的图形界面，不需要背命令。队长先做第一部分，然后五个成员照第二部分做。

> 界面语言：GitHub Desktop 官方只有英文。按钮的中英文对照见 `docs/12-github-desktop-english-cheatsheet.md`，照着点即可。

先理解三个东西：

- **本地文件**：`D:\课程\CS5351_Software-Engineering\project` 这个文件夹。
- **本地仓库**：文件夹里的 `.git`，记录每次修改的历史。
- **GitHub 远程仓库**：网页上的副本，团队成员通过它同步代码。

提交（commit）是"拍一张本地快照"，推送（push）是"把快照上传到 GitHub"。

---

## 第一部分：队长 30 分钟

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

### 4. 第一次提交（你的第一条工作记录）

在 GitHub Desktop 左侧勾选下面这些文件（保留 `out/` 不勾，它已经被忽略）：

- `.gitignore`
- `TEAM.md`
- `README.zh-CN.md`
- `docs/09-topic-introduction-for-ta.md`
- `docs/10-github-team-workflow.md`
- `docs/11-github-desktop-beginner-guide.md`
- `docs/process/two-week-plan.md`
- `scripts/check-team-records.ps1`

在左下角填写：

- **Summary**：`chore: add team roster and two-week plan`
- **Description**：`Adds team roles, GitHub workflow, beginner guide and the schedule up to the presentation.`

点 **Commit to main**。

### 5. 发布到 GitHub

1. 顶部会出现 **Publish repository**，点击。
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
   验收：视频不超过 7 分钟，包含完整演示，彩排计时记录在 PR 里。

6. **M6 报告**：`report: IEEE TSE formatting, bios and contribution table`
   验收：报告含 6 人简介、self-reflection、贡献表和全部图表。

---

## 第四部分：每天怎么用

- **开始工作前**：GitHub Desktop 点 **Fetch origin → Pull origin**。
- **做完一小步**：Commit 一次，Summary 用一句话说清楚。
- **完成一个任务**：Push → PR → 找人 review → 合并。
- **每周日**：更新 `docs/process/weekly-evidence.md`，写清本周谁做了什么、对应哪个 Issue/PR。
- **提交前检查**：

```powershell
.\scripts\check-team-records.ps1 -Members "姓名1","姓名2","姓名3","姓名4","姓名5","姓名6"
```

---

## 第五部分：常见问题

**Q：GitHub Desktop 显示 "No local changes"，但我改了文件？**
确认你改的是 `Clone` 下来的那个文件夹，不是桌面上的旧副本。

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
