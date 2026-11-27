TASK_ID: IDEA_XHS_DAILY_CLUES_V3_20261127
TASK_VERSION: 3
STATUS: BLOCKED_WAITING_AUTHORIZED_INPUT
NEXT_ACTOR: GEMINI

# idea checker 自动任务回执

- Checker安装：VERIFIED（Windows 计划任务 `idea-OpenCode-10min` 已注册并启用，每 10 分钟轮询；上次运行 2026/11/27 20:29:18 结果 0）
- OpenCode投递：DONE（已领取并执行 v3）
- 具体执行结果：见 `OPENCODE_REPORT_XHS_DAILY.md`
- 结果摘要：小红书经管选题线索框架 v3 本地执行。单测 9/9 通过；本地模板已初始化（`data/xhs/*.template.csv`）；轨道 A 获准线索 CSV **不存在** → `BLOCKED_WAITING_AUTHORIZED_INPUT`（0 输入/0 有效/0 拒绝，未抓取、未生成 latest.json）；轨道 B 一手源 CSV 不存在 → 0 条；定时任务核查通过（未新建重复任务）。
- 状态说明：BLOCKED_WAITING_AUTHORIZED_INPUT。需用户/获准本地导出流程提供 `data/xhs/daily_approved_clues.csv` 后方可入库；公开索引一手源需 `data/xhs/public_clue_leads.csv`。
- 本文件由 OpenCode 在真实本地执行后更新。
