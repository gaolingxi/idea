TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 2
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_NSSFC_2026_FULL_ROSTER.md;scripts/audit_nssfc_2026_full_proposed.py;OPENCODE_REPORT_NSSFC_2026_PDF.md;AGENTS.md

# 当前任务：国社科2026拟立项完整6065行审计

前序PDF下载提取任务（v3）已DONE，5931条公开题目已经核实。本任务负责从四份原PDF保留134条“题目略”的公示项目，核对四类总计6065条并在全部质量闸门通过后写入公开索引。执行入口：OPENCODE_TASK_AUTORUN.md。OpenCode只执行ChatGPT写好的脚本。

## v2 本轮修复说明
四份原PDF表头为「申请人」，v1 脚本的 person 列词表遗漏该名称导致0行、已如实报告FAILED。v2 只修复该表头，测试已改用真实表头；重新运行原四份PDF的完整6065行审核，严禁跳过质量闸门或把拟立项当正式立项。原 v1 FAILED 报告保留作证据。
