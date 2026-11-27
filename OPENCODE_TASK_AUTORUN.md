TASK_ID: IDEA_ECON_DATA_AUDIT_V1_20261127
TASK_VERSION: 1
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_ECON_AUDIT.md;scripts/crawl_official_sites.py;scripts/grant_hourly_monitor.py;sources/site_registry.json;AGENTS.md

# idea checker 自动领取｜经济学原始资料层质量排查（v1）

1. 在 `idea/repo` 确认工作树安全且 `TASK_ID`/`TASK_VERSION` 一致，正常同步 `origin/main`，核对 `AGENTS.md` 与 `STAGE_PLAN.md`。
2. 执行 `OPENCODE_TASK_ECON_AUDIT.md`：只读定位日期截断 Bug、24 个月过滤缺口、以及会议论文/发改委/工信部 0 条原因，不修改脚本与数据文件。
3. 回写 `OPENCODE_REPORT_ECON_AUDIT.md` 和 `OPENCODE_REPORT_AUTORUN.md`（带 `TASK_ID: IDEA_ECON_DATA_AUDIT_V1_20261127`、`TASK_VERSION: 1`、`STATUS: DONE`、`NEXT_ACTOR: GEMINI` 及提交 SHA），提交并推送到 `origin/main`。单次执行即止，不自行新增计划任务。
