TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 1
STATUS: FAILED
NEXT_ACTOR: ChatGPT

# idea checker 自动任务回执

- Checker安装：VERIFIED（Windows 计划任务 `idea-OpenCode-10min` 已注册）
- OpenCode投递：DONE（已领取并执行）
- 具体执行结果：见 `OPENCODE_REPORT_NSSFC_2026_FULL_ROSTER.md`
- 结果摘要：审计脚本 `audit_nssfc_2026_full_proposed.py` 因 `header_map` 的 person 词表漏「申请人」（4 份 PDF 表头为「申请人」，非「负责人」）而四类全部提取 0 行，质量闸门拒绝发布。未生成公开 CSV，无假入库。
- 状态说明：FAILED（脚本缺陷，非访问限制）。需 ChatGPT 将 `header_map` person 词表加「申请人」后重发；OpenCode 不改代码。
- 本文件由 OpenCode 在真实本地执行后更新。
