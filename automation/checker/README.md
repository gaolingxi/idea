# Canonical Project Checker Template

这是新研究项目默认使用的 **GitHub → checker → Orca/OpenCode** 本地自动领取模板。

目标只有一个：ChatGPT/总控在 GitHub 发布一个已经冻结、可机械执行的任务后，本地 checker 每 10 分钟自动发现，并向该项目现有的 OpenCode 窗口发送一次 `继续`。checker 不做研究设计、不修改研究代码、不启动新 OpenCode、不承担结果判断。

## 默认架构

```text
ChatGPT/总控
  ↓ GitHub
CURRENT_TASK.md + OPENCODE_TASK.md
  ↓ 本地每10分钟
checker.py
  ↓ 找到“本项目 worktree”唯一有效 OpenCode
发送一次：继续 + Enter
  ↓
OpenCode 执行冻结任务
  ↓ GitHub
OPENCODE_REPORT.md / PROJECT_SYNC.md
  ↓
下一轮总控审核 → 发布下一任务
```

checker 同时通过 GitHub commit status 回传本地领取状态，因此总控可以直接看到 `CONTINUE_SENT / BUSY / NOT_FOUND / AMBIGUOUS / DEDUPED / ERROR`，不需要依赖 Remote Desktop 判断本地发生了什么。状态内容发生变化时才重新发布，避免每 10 分钟制造重复状态。

**默认不使用 shared route。** 每个项目只绑定自己的 repo/worktree，直接用 `TASK_ID + TASK_VERSION + 当前任务文件 blob` 去重。这从结构上避免旧 `SENT` route 长期占位导致新任务 `SHARED_ORCA_BUSY`。

## 已吸收的故障修复

这个模板统一吸收当前各项目已经验证过的经验：

- terminal handle 只是 preferred hint，不是永久身份；handle 失效但只有一个有效 OpenCode 时自动重发现；
- 0 个候选返回 `ORCA_OPENCODE_NOT_FOUND`；多个候选返回 `ORCA_OPENCODE_AMBIGUOUS`，绝不猜；
- OpenCode busy 时不发送，保持任务下一轮可重试；
- 只有 Orca 明确 `send accepted` 后才记录已发送；
- focus/switch 最多重试两次；focus 失败不能重复发送 `继续`；
- 本地去重只针对同一个 `TASK_ID + TASK_VERSION + fingerprint`；旧任务记录永远不能挡不同新任务；
- checker 锁具有 stale recovery，异常退出留下的孤儿锁不会永久阻塞；
- Windows Scheduled Task 直接通过仓库内 `scheduled_entry.ps1` 定位当前 checker，不运行 AppData 中脱离 GitHub 的 watcher 旧副本；
- checker 只 `git fetch` + `git show origin/<branch>:...`，不 pull/merge，不干扰 OpenCode 当前工作树；
- 默认隐藏运行，不弹 PowerShell/CMD 黑窗；
- checker 状态通过 GitHub commit status 回传，不修改科研文件，因此不会和 OpenCode/ChatGPT 的 Git push 冲突；
- checker 不把 `BLOCKED` 当研究终点。科研 REPORT 由总控遵循“跑完了 → 审核 → 下一步”处理。

## 新项目接入

把本目录复制到新仓库的：

```text
automation/checker/
```

将 `config.example.json` 复制为 `config.json`，至少修改：

```json
{
  "schema_version": 1,
  "repository_slug": "gaolingxi/NEW-PROJECT",
  "branch": "main",
  "poll_minutes": 10,
  "enabled": true,
  "publish_github_status": true,
  "github_status_context": "local-checker/NEW-PROJECT"
}
```

项目根目录至少维护：

```text
CURRENT_TASK.md
OPENCODE_TASK.md
OPENCODE_REPORT.md
```

当前任务要自动领取时，`CURRENT_TASK.md` 和 `OPENCODE_TASK.md` 顶部元数据至少保持：

```text
TASK_ID: UNIQUE_TASK_ID
TASK_VERSION: 1
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: path/a.do;path/b.md
```

`TASK_ID`、`TASK_VERSION`、`STATUS`、`EXECUTOR`、`AUTOMATION_READY` 必须在 CURRENT/TASK 两个文件一致。

## 安装前模板验收

```powershell
powershell -ExecutionPolicy Bypass -File automation/checker/verify_template.ps1
```

它会检查：

1. `checker.py` Python 语法；
2. checker 单元测试；
3. `install_windows.ps1` PowerShell 语法；
4. `scheduled_entry.ps1` PowerShell 语法。

## 安装

在项目本地运行一次：

```powershell
powershell -ExecutionPolicy Bypass -File automation/checker/install_windows.ps1
```

安装器会：

1. 验证仓库与 `config.json`；
2. 使用仓库内隐藏启动器；
3. 创建 `<project>-OpenCode-10min` Windows Scheduled Task；
4. 计划任务每 10 分钟执行仓库当前版本 `scheduled_entry.ps1`；
5. 不复制 checker 到 AppData。

GitHub 状态回传使用本机已登录的 `gh` CLI；若 `gh` 不可用，checker 的任务领取仍正常，只是本轮不会发布 commit status。

## 任务验收

```powershell
python automation/checker/checker.py --repo . --check
```

可能状态：

- `READY_CHECK_ONLY`：任务可领取；
- `ORCA_CONTINUE_SENT`：已成功向现有 OpenCode 发送一次 `继续`；
- `IDLE_ALREADY_CONTINUED`：当前任务已经发送过，不重复执行；
- `ORCA_OPENCODE_BUSY`：OpenCode 正在工作，下轮再试；
- `ORCA_OPENCODE_NOT_FOUND`：没有当前项目 OpenCode；
- `ORCA_OPENCODE_AMBIGUOUS`：当前项目存在多个有效 OpenCode，需先消除歧义；
- `IDLE_NO_EXECUTABLE_TASK`：当前没有可自动执行任务。

## 不应加入默认 checker 的功能

以下内容不属于 checker：

- 研究方案判断；
- Stata/Python 科研代码生成；
- 自动降低科学 Gate；
- 根据 p 值自动换模型；
- 自动创建下一科研任务；
- 多项目优先级调度；
- 复杂 shared route / 跨项目终端复用。

这些由 ChatGPT 定时总控和各项目研究规则负责。

## 版本原则

本目录是新项目 checker 的**唯一模板源**。以后发现共性 checker bug，优先先修这里，再判断哪些已存在项目需要同步；不要再从某个历史项目复制旧 watcher 作为新项目起点。
