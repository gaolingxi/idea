# AGENTS.md — 原始资料层
当前只做滚动24个月政策、学术会议论文、科研立项与小红书原始资料的采集；不做选题评分或回归。
- ChatGPT 写完整代码；OpenCode 只运行和提交报告。
- 本项目内的 `data/`、`logs/` 为本地保存目录，不允许保存到仓库之外。
- 仓库公开：绝不提交任何用户数据、笔记正文、凭证、私密资料。
- 小红书采集必须具备明确的合法许可，不绕过登录、验证码、403/429、robots 或平台服务协议；没有权限则停止并报告。
- 缺失发布日期不能视为过去24个月有效样本。
- 需要时渐进阅读：`OPENCODE_TASK.md` → `scripts/xhs_approved_ingest.py` → `OPENCODE_REPORT.md`。

## 公开科研名单附件的本地执行器转交规则
- 若ChatGPT云端检索只能看到官方公告但无法取得其公开PDF/Excel真实下载链接，先核验公告来源，再编写**限定单一来源的OpenCode任务与现成脚本**，放在独立任务文件中，不覆盖其他根任务。
- OpenCode负责在本地授权、正常网络条件下运行脚本并记录真实下载URL、结果、附件数量及表格逐题提取数；ChatGPT负责后续核验和脚本修订。
- 文件使用项目内`data/`和`logs/`；一律不绕过robots、403/429、验证码、登录等权限限制。抓不到就明确报告BLOCKED。不能把拟立项公示冒充正式立项。
- 每条本地任务必须维护对应`OPENCODE_TASK_*.md`与`OPENCODE_REPORT_*.md`；本地连接离线时状态只可标记READY/NOT_RUN，不能声称OpenCode已执行。

## idea 项目 checker（基础设施，非科研任务）
- 采用 `gaolingxi/research-project-orchestrator/checker-template` 标准模板，位于 `automation/checker/`；只轮询 **gaolingxi/idea** 的 `origin/main`，每10分钟检查一次。
- 当前独立自动入口为 `CURRENT_TASK.md` + `OPENCODE_TASK_AUTORUN.md`；具体当前任务详见其引用的 `OPENCODE_TASK_NSSFC_2026_PDF.md`。原有 `OPENCODE_TASK.md` 小红书权限审查任务与报告**不修改**。
- 任务仅在 `TASK_ID/TASK_VERSION/STATUS/EXECUTOR/NEXT_ACTOR/AUTOMATION_READY` 等元数据一致且必需文件齐全时投递；成功只向该项目 **唯一、可写、空闲的现有 Orca OpenCode** 发送一次“继续”+Enter，不创建新进程，不将指令发往其他仓库的 OpenCode。
- 未找到唯一窗口、忙碌、任务不符、没有本地安装回执时只报告状态，不能标记已领取；窗口句柄变更自动重发现，陈旧锁可回收。
- 本地安装仅在本项目仓库文件夹执行一次 `powershell -ExecutionPolicy Bypass -File automation/checker/install_windows.ps1`。安装前使用 `automation/checker/verify_template.ps1`。Windows计划任务执行仓库当前版本的薄入口，不把 watcher 复制到AppData。
- Checker 只读 GitHub 任务并回传领取状态，不修改研究代码/任务结果；OpenCode回写 `OPENCODE_REPORT_AUTORUN.md` 和对应子任务报告。未经真实本地计划任务回执，`checker已部署到GitHub`**不等于**`Windows定时器已安装/已投递`。
