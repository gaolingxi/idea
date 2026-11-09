TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 2
STATUS: FAILED
NEXT_ACTOR: ChatGPT

# idea checker 自动任务回执

- Checker安装：VERIFIED（Windows 计划任务 `idea-OpenCode-10min` 已注册）
- OpenCode投递：DONE（已领取并执行 v2）
- 具体执行结果：见 `OPENCODE_REPORT_NSSFC_2026_FULL_ROSTER.md`
- 结果摘要：v2 修复 `申请人` 表头后四类提取 444/2705/2350/566 成功、公开 5931+略 134 闸门通过；但第 3 道闸门因**类别标签不一致**（审计脚本用英文 key/general/young/western，v3 CSV 用中文 重点/一般/青年/西部）而失败；忽略类别后内容 (title,person,unit) 完全一致（0 差）。
- 状态说明：FAILED（脚本比较闸门类别标签未归一化，非访问限制、非内容差异）。需 ChatGPT 将比较归一化后重发；OpenCode 不改代码。
- 本文件由 OpenCode 在真实本地执行后更新。
