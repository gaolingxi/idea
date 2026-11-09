TASK_ID: IDEA_NSSFC_2026_SU_SE_PDF_LINKS_V1
TASK_VERSION: 3
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_NSSFC_2026_PDF.md;scripts/inspect_nssfc_2026_pdf_links.py;requirements-site-crawler.txt;AGENTS.md

# idea 自动领取任务（调度入口）

版本3修复白名单声明被意外注释的代码问题；已限定允许访问大学公告域和经核验的 `download.people.com.cn`，重新执行4份PDF下载、逐题提取和抽查；拟立项不得计为正式立项。

收到 Orca 的“继续”后，在 `gaolingxi/idea` **本项目根目录**执行：

1. 用 `git fetch origin main` 查看最新任务。若工作树干净且没有本地未提交变更，使用 `git pull --ff-only origin main` 同步；否则保持原数据不变并在独立报告记录阻塞。
2. 只读取 `AGENTS.md`、`CURRENT_TASK.md`、`OPENCODE_TASK_AUTORUN.md` 和 `OPENCODE_TASK_NSSFC_2026_PDF.md`，按后者指令执行已由 ChatGPT 编写的 `scripts/inspect_nssfc_2026_pdf_links.py`。OpenCode **不得**自行新建替代爬虫或改变研究任务。
3. 结果写回 `OPENCODE_REPORT_NSSFC_2026_PDF.md`，并更新 `OPENCODE_REPORT_AUTORUN.md` 的 `TASK_ID`、`TASK_VERSION`、`STATUS`（DONE / BLOCKED / FAILED）与证据链接。GitHub 中只提交报告和公开元数据，不提交 data/ 下PDF、数据库和访问凭证。
4. 若无法访问官方公开网页、需要验证码/登录、或找不到相同 worktree 的唯一 OpenCode，明确报告 BLOCKED，停止。本项目之外的窗口/文件一律不碰。

严格只执行这一项；完成后不自行生成新的科研或抓取任务。由 ChatGPT 审核新报告并发布下一版本。
