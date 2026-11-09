TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 2
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_NSSFC_2026_FULL_ROSTER.md;scripts/audit_nssfc_2026_full_proposed.py;OPENCODE_REPORT_NSSFC_2026_PDF.md;AGENTS.md

# idea自动领取任务｜第4阶段：全量公示名册

收到本项目 Orca OpenCode 的“继续”后，只执行 OPENCODE_TASK_NSSFC_2026_FULL_ROSTER.md：

1. git fetch origin main，本地仓库无修改时使用 git pull --ff-only origin main 同步。
2. 阅读 AGENTS.md 和本次专项任务，运行 scripts/audit_nssfc_2026_full_proposed.py。无需重新下载4份PDF；不得改动原科研数据，不得修改或补造“题目略”。
3. 只在6065项目总量、类别计数、5931公开题目一致性及134缺标题统计全部通过时，提交公开公示元数据CSV及审计报告。
4. 回写 OPENCODE_REPORT_NSSFC_2026_FULL_ROSTER.md 和 OPENCODE_REPORT_AUTORUN.md 的TASK_ID/TASK_VERSION/STATUS及结果。没有成功则记BLOCKED/FAILED和具体原因。
5. 完成后交ChatGPT审阅，不开展其他任务、不创建新主线。

## v2 本轮修复说明
四份原PDF表头为「申请人」，v1 脚本的 person 列词表遗漏该名称导致0行、已如实报告FAILED。v2 只修复该表头，测试已改用真实表头；重新运行原四份PDF的完整6065行审核，严禁跳过质量闸门或把拟立项当正式立项。原 v1 FAILED 报告保留作证据。
