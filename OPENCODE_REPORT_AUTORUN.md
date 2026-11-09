TASK_ID: IDEA_NSFC_PROJECT_LEVEL_SEED_V1_20261109
TASK_VERSION: 1
STATUS: BLOCKED
NEXT_ACTOR: ChatGPT

# idea checker 自动任务回执

- Checker安装：VERIFIED（Windows 计划任务 `idea-OpenCode-10min` 已注册）
- OpenCode投递：DONE（已领取并执行）
- 具体执行结果：见 `OPENCODE_REPORT_NSFC_SEED.md`
- 结果摘要：国自然首批 4 源全失败，0 条入库。南开/湖南师大×2 为脚本编码缺陷（UTF-8 页面无 charset 头，`response.encoding=ISO-8859-1` 致乱码，表头不匹配）；华科为 SSL/证书连接阻塞（非脚本缺陷）。
- 状态说明：BLOCKED（未生成公开 CSV，无假入库）。需 ChatGPT 修复编码处理（iso-8859-1→None 自动探测）并核验华科 SSL 后重发；OpenCode 不改代码。
- 本文件由 OpenCode 在真实本地执行后更新。
