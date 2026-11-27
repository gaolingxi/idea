TASK_ID: IDEA_ECON_DATA_AUDIT_V1_20261127
TASK_VERSION: 1
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_ECON_AUDIT.md;scripts/crawl_official_sites.py;scripts/grant_hourly_monitor.py;sources/site_registry.json;AGENTS.md

# 当前任务：经济学原始资料层质量排查（日期截断 / 会议论文 / 24个月过滤）

子任务：`OPENCODE_TASK_ECON_AUDIT.md`。说明：小红书线索采集已改由本地 `pi` 负责，OpenCode 不再执行小红书任务；国社科（6065 条）冻结保留，国自然 v2（46 条）保留。本轮仅做代码级只读排查并回写 `OPENCODE_REPORT_ECON_AUDIT.md` 与 `OPENCODE_REPORT_AUTORUN.md`（`NEXT_ACTOR: GEMINI`），同时验证本地事件驱动闭环。
