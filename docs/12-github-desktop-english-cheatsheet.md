# GitHub Desktop 英文界面对照表

GitHub Desktop 官方界面只有英文，没有内置中文。建议直接用英文界面配这张表，不要安装第三方汉化补丁：补丁通常修改程序文件，Desktop 自动更新后会失效，来源也无法验证。

## 你会用到的按钮

| 英文 | 中文 | 什么时候点 |
| --- | --- | --- |
| Sign in to GitHub.com | 登录 GitHub | 第一次打开 Desktop |
| File → Add local repository | 文件 → 添加本地仓库 | 队长把已有项目加进来 |
| File → Clone repository | 文件 → 克隆仓库 | 成员把远程仓库下载到电脑 |
| Current branch | 当前分支 | 切换分支 |
| New branch | 新建分支 | 开始一个新任务 |
| Changes | 更改 | 查看自己改了哪些文件 |
| Summary | 提交说明（必填） | 一句话说明这次改了什么 |
| Description | 详细说明（选填） | 补充原因或验证方式 |
| Commit to main | 提交到 main | 第一次提交，还没有分支时 |
| Commit to <branch> | 提交到当前分支 | 正常开发时 |
| Publish repository | 发布仓库 | 第一次把本地仓库传到 GitHub |
| Publish branch | 发布分支 | 第一次把新分支传到 GitHub |
| Push origin | 推送到远程 | 之后每次提交完上传 |
| Fetch origin | 获取远程更新 | 每天开始工作前 |
| Pull origin | 拉取远程更新 | 获取后把别人的改动合并到本地 |
| Create Pull Request | 创建合并请求 | 分支推送后，请别人审核 |
| Files changed | 更改的文件 | 在网页上查看 PR 改了什么 |
| Review changes | 审核更改 | 给同学的 PR 写意见 |
| Approve | 批准 | 审核通过 |
| Merge pull request | 合并请求 | 审核通过后合并进 main |
| Confirm merge | 确认合并 | 最后确认 |
| History | 历史 | 查看提交记录 |
| Undo | 撤销 | 撤销最近一次提交（不会删除文件） |
| Discard changes | 丢弃更改 | **危险**：删除你还没提交的修改 |
| Repository settings | 仓库设置 | 查看远程地址等 |
| Open in Visual Studio Code | 用 VS Code 打开 | 开始改代码 |
| Show in Explorer | 在资源管理器中显示 | 找到本地文件夹 |

## 完整流程（照着顺序点）

1. **Fetch origin** → **Pull origin**：先拿最新代码。
2. **Current branch → New branch**：输入 `sprint-3/us-21-你的名字`，点 Create branch。
3. 改文件，回到 Desktop，左侧会列出改动。
4. 勾选要提交的文件（不要把 `out/`、`.risktest/`、`.pytest_cache/`、`__pycache__/` 勾上；`.gitattributes` 要保留）。
5. 填 **Summary**，例如 `US-21: add selector edge-case tests`。
6. 点 **Commit to <branch>**。
7. 点 **Publish branch**（第一次）或 **Push origin**（以后）。
8. 点 **Create Pull Request**，浏览器打开后点 **Create pull request**。
9. 找同学在 **Files changed → Review changes → Approve**。
10. 你点 **Merge pull request → Confirm merge**。
11. 回 Desktop 点 **Fetch origin → Pull origin**。

## 界面上的几个提示

- **"Commit anyway"**：有些检查没通过时的确认按钮。先看清楚原因，不要无脑点。
- **"This branch is X commits ahead"**：你的分支比远程多 X 个提交，点 **Push origin** 上传。
- **"This branch is X commits behind"**：远程有别人的新提交，点 **Pull origin** 同步。
- **"Conflicts"**：两边改了同一行。不要点 **Discard changes**，找队长一起解决。
- **"Discard changes"**：会永久删除未提交的修改，确认前先看清楚。
- **"This file uses 'LF' line endings, but Git is configured to convert them to 'CRLF'..."**：换行符提示，不是错误。见下一节。

## 换行符提示（LF / CRLF）

仓库已经用 `.gitattributes` 统一了规则：

- 文本文件（`.py`、`.md`、`.json`、`.csv` 等）用 **LF**；
- PowerShell 脚本（`.ps1`）和 `.bat` 用 **CRLF**；
- `.pptx`、`.xlsx`、图片按**二进制**处理，不做转换；
- 仓库本地设置了 `core.autocrlf=false`，不再自动把 LF 改成 CRLF。

如果 Desktop 仍然显示这条提示：

1. 这不是报错，文件可以正常提交。
2. 直接点 **Commit to main** 或 **Commit to <branch>**。
3. **不要点 Discard changes**，那会丢掉你还没提交的修改。
4. 不要安装第三方"换行符修复工具"。
5. 关掉 Desktop 再打开；仍然出现就把提示发到群里。

## 网页版语言

GitHub 网页版是否提供中文取决于账号当前开放的界面语言。打开 https://github.com/settings/appearance ，查看 **Language** 是否有简体中文；没有的话，网页版也用英文，常用的只有 **Issues**、**Pull requests**、**Settings**、**Collaborators**、**Branches** 这几个词。

| 网页英文 | 中文 |
| --- | --- |
| Issues | 问题/任务 |
| New issue | 新建任务 |
| Pull requests | 合并请求 |
| New pull request | 新建合并请求 |
| Reviewers | 审核人 |
| Merge pull request | 合并 |
| Settings | 设置 |
| Collaborators | 协作者 |
| Branches | 分支 |
| Insights → Contributors | 洞察 → 贡献者 |
| Actions | 自动化（CI） |
