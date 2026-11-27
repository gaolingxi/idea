TASK_ID: IDEA_ECON_DATA_AUDIT_V1_20261127
TASK_VERSION: 1
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_ECON_AUDIT.md;scripts/crawl_official_sites.py;scripts/grant_hourly_monitor.py;sources/site_registry.json;AGENTS.md

# 经济学原始资料层质量排查（日期截断 + 会议论文缺口 + 过时公告）

说明：按用户最新分工，**小红书线索采集已改由本地 `pi` 负责，OpenCode 不再处理小红书任务**；OpenCode 专注学术会议论文、政策文件与科研立项数据质量。

## 本轮目标（只读排查 + 报告，不修改数据文件与脚本）
1. **同步与自检**：同步 `origin/main`，核对 `AGENTS.md` 与 `STAGE_PLAN.md`。
2. **定位日期截断 Bug**：检查 `scripts/crawl_official_sites.py` 与 `scripts/grant_hourly_monitor.py` 中解析发布日期的正则/逻辑，找出导致 `2025/0728 -> 2025-07-02`、`2026/10/30 -> 2026-10-03`、`[2026年11月10日] -> 2026-11-01` 的精确文件路径与行号。
3. **定位 24 个月过滤缺口**：检查 `scripts/grant_hourly_monitor.py`，说明为何 `public_metadata/grant_source_notices.csv` 中混入了 2016–2023 年旧公告及 86 条缺日期记录。
4. **定位会议论文与部委政策 0 条原因**：检查 `sources/site_registry.json` 与 `scripts/crawl_official_sites.py`，说明为何 `conference_cea_2025_attachment`、`conference_cfrc_2025`、`conference_cfrc_2026`、`policy_ndrc`、`policy_miit` 在 `public_metadata/official_source_pages.csv` 中为 0 条（不发起大规模爬取，仅代码级定位）。
5. **回写报告并触发闭环**：
   - 写入 `OPENCODE_REPORT_ECON_AUDIT.md`（列出上述 3 项定位结论、代码行号与修复建议）。
   - 更新 `OPENCODE_REPORT_AUTORUN.md`，必须包含：
     - `TASK_ID: IDEA_ECON_DATA_AUDIT_V1_20261127`
     - `TASK_VERSION: 1`
     - `STATUS: DONE`
     - `NEXT_ACTOR: GEMINI`
   - 提交并推送报告文件。
