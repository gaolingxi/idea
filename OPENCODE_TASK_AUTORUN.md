TASK_ID: IDEA_XHS_DAILY_CLUES_V1_20261125
TASK_VERSION: 2
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_XHS_DAILY.md;scripts/prepare_xhs_daily_clues.py;AGENTS.md

# idea checker 自动领取｜小红书合规线索交接

1. 在 idea/repo 确认工作树安全且当前任务 ID/version 一致，正常同步 origin/main。
2. 执行 OPENCODE_TASK_XHS_DAILY.md。先检查合法获准的本地输入是否存在，运行已提交脚本 `python scripts/prepare_xhs_daily_clues.py`（有合格输入才整理；缺少输入应如实 BLOCKED）。
3. 审查合格输出，只有明确许可公开分享的短研究概念及必要来源元数据可提交 `sources/xhs_daily/latest.json`；绝不上传原始笔记或用户数据、凭证。
4. 回写 OPENCODE_REPORT_XHS_DAILY.md 和 OPENCODE_REPORT_AUTORUN.md，带 TASK_ID、TASK_VERSION、实际状态、NEXT_ACTOR: ChatGPT、条数、各账号覆盖和阻塞原因；实际成功才报告提交 SHA。没有许可不得绕过平台限制。单次执行即止，不自行新增计划任务。
