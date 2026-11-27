TASK_ID: IDEA_XHS_DAILY_CLUES_V3_20261127
TASK_VERSION: 3
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: sources/xhs_account_registry.json;OPENCODE_TASK_XHS_DAILY.md;scripts/prepare_xhs_daily_clues.py;AGENTS.md

# idea checker 自动领取｜小红书经管选题线索日更框架（v3）

1. 在 `idea/repo` 确认工作树安全且 `TASK_ID`/`TASK_VERSION` 一致，正常同步 `origin/main`，核对 `AGENTS.md` 与 `STAGE_PLAN.md`。
2. 运行 `python -m unittest discover -s tests -p "test_xhs*.py" -v` 验证脚本与账号注册表正常。
3. 执行 `OPENCODE_TASK_XHS_DAILY.md`：初始化 `data/xhs/` 模板；若存在获准本地输入 `data/xhs/daily_approved_clues.csv`（或 `data/xhs/public_clue_leads.csv`），运行 `python scripts/prepare_xhs_daily_clues.py --registry sources/xhs_account_registry.json --window-days 14`；缺少获准输入时如实报告 BLOCKED，不抓取平台、不覆盖旧快照。
4. 审查合格输出后仅提交允许公开的脱敏 JSON 与报告；回写 `OPENCODE_REPORT_XHS_DAILY.md` 和 `OPENCODE_REPORT_AUTORUN.md`（带 `TASK_ID`、`TASK_VERSION`、实际状态、`NEXT_ACTOR: GEMINI`、单测/模板/轨道 A/轨道 B/定时任务核查结果与提交 SHA）。单次执行即止，不自行新增计划任务。
