TASK_ID: IDEA_XHS_DAILY_CLUES_V3_20261127
TASK_VERSION: 3
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: sources/xhs_account_registry.json;OPENCODE_TASK_XHS_DAILY.md;scripts/prepare_xhs_daily_clues.py;AGENTS.md

# 当前任务：小红书经管选题线索日更框架与本地执行（v3）

子任务：`OPENCODE_TASK_XHS_DAILY.md`；账号与主题框架：`sources/xhs_account_registry.json`。国社科（6065 条）冻结保留，国自然 v2（46 条，PARTIAL_DONE）保留。本次升级为注册表驱动 + 双轨合规日更框架（轨道 A：本地获准 CSV -> `sources/xhs_daily/latest.json` + 每日快照；轨道 B：公开一手源回溯 -> `sources/xhs_daily/verified_public_leads.json`）。无获准输入时生成本地模板并如实报告 BLOCKED，严禁绕过平台限制或伪造记录。
