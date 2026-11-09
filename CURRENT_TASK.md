TASK_ID: IDEA_NSSFC_2026_SU_SE_PDF_LINKS_V1
TASK_VERSION: 3
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_NSSFC_2026_PDF.md;scripts/inspect_nssfc_2026_pdf_links.py;requirements-site-crawler.txt;AGENTS.md

# 当前自动执行任务：国社科2026公告PDF

这不是小红书任务；只指向 `OPENCODE_TASK_AUTORUN.md` 和其中所引用的 `OPENCODE_TASK_NSSFC_2026_PDF.md`。checker 仅在上述文件均存在、元数据一致时向本项目现有 OpenCode 发送一次“继续”。

本地安装状态：VERIFIED（见 OPENCODE_REPORT_AUTORUN.md）。上一版本已领取但因外部附件域名白名单而 BLOCKED；版本3修复了脚本中的转义换行错误，确保 download.people.com.cn 白名单在Python运行时真正生效。请重新运行同一公告的4份PDF并回写实际结果；不得提前标记成功。
