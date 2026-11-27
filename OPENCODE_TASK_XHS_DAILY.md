TASK_ID: IDEA_XHS_DAILY_CLUES_V3_20261127
TASK_VERSION: 3
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: sources/xhs_account_registry.json;OPENCODE_TASK_XHS_DAILY.md;scripts/prepare_xhs_daily_clues.py;AGENTS.md

# 每日小红书经管选题线索框架｜本地 Orca OpenCode 执行任务（v3）

本任务由 Gemini 按 `STAGE_PLAN.md` 阶段协作框架布置给本地 Orca OpenCode 执行。不覆盖已冻结的国社科（6065 条）和国自然 v2（46 条）历史任务与数据。

## 一、账号与主题框架（以 `sources/xhs_account_registry.json` 为准）
脚本不再硬编码账号，统一读取 `sources/xhs_account_registry.json`：
- **Tier 1 核心追踪账号（已入库，4 个）**：
  1. `Kenny思享` — 顶刊速递与学术会议 / 实证方法 / 宏观政策
  2. `大山经管资料` — 微观数据库与因果推断 / 政策资料 / 基金立项
  3. `iiiiop` — 经管科研思路与文献线索
  4. `土豆学姐（研究ing）` — 科研基金与投稿选题进展
- **Tier 2 扩展槽位（4 类，须人工核实真实账号名后方可迁入 `accounts`）**：
  - `policy_macro`（宏观与产业政策解读）
  - `empirical_data`（微观数据库与因果推断）
  - `journal_conference`（顶刊速递与学术会议）
  - `grant_funding`（国自然管理科学部 / 国社科应用经济学立项复盘）

## 二、合规红线（必须严格遵守）
1. **绝不**绕过小红书登录墙、验证码、403/429、robots 或平台服务协议；**绝不**自动登录、提取 Cookie、调用私有接口或模拟浏览器规避限制。
2. **绝不**向公开仓库提交 `data/`、`logs/`、笔记正文、标题全文、截图、评论、个人隐私或授权凭证。
3. 缺失发布日期或超出滚动时间窗的记录一律拒绝，绝不伪造记录或虚报条数。

## 三、双轨日更执行步骤（Orca OpenCode 逐项执行）
1. **环境与代码自检**
   - 确认工作树安全并同步 `origin/main`，核对 `AGENTS.md` 与 `STAGE_PLAN.md`。
   - 运行单元测试：`python -m unittest discover -s tests -p "test_xhs*.py" -v`，确保全部通过。
2. **初始化本地模板（仅本地 `data/xhs/`，不提交 Git）**
   - 运行：`python scripts/prepare_xhs_daily_clues.py --init-template`
   - 确认生成 `data/xhs/daily_approved_clues.template.csv` 和 `data/xhs/public_clue_leads.template.csv`。
3. **轨道 A：获准小红书线索入库（主轨）**
   - 检查本地是否存在 `data/xhs/daily_approved_clues.csv`（由用户或获准本地导出流程提供）。
   - 若存在且包含合格行：运行 `python scripts/prepare_xhs_daily_clues.py --registry sources/xhs_account_registry.json --window-days 14`，生成/更新 `sources/xhs_daily/latest.json` 及按日快照 `sources/xhs_daily/snapshots/YYYY-MM-DD.json`。
   - 审查输出 JSON，确认仅包含：公开账号名、主题分类、发布日期、去参数原帖链接、简短研究概念（<=80 字）、可选的一手公开来源链接与审核状态，无任何正文/隐私/凭证。
   - 若不存在或有效条数为 0：如实记录 `BLOCKED_WAITING_AUTHORIZED_INPUT`，不抓取平台、不覆盖旧快照。
4. **轨道 B：公开索引回溯一手源（补充轨，不碰小红书受限页）**
   - 若本地存在 `data/xhs/public_clue_leads.csv`（从公开搜索引擎/高校官网/部委官网/学术会议页独立核实的 24 个月内政策/论文/立项一手链接），脚本将同步生成 `sources/xhs_daily/verified_public_leads.json`，明确标记 `public_search_traced_primary_source`（不得声称看过小红书原帖）。
5. **每日定时触发状态核查**
   - 仅核查现有 Windows 计划任务 `idea-OpenCode-10min` 的运行状态与上次执行时间（不擅自新建重复任务），确认是否已能持续轮询。
6. **回写报告与交接**
   - 更新 `OPENCODE_REPORT_XHS_DAILY.md` 和 `OPENCODE_REPORT_AUTORUN.md`：
     - 标明 `TASK_ID: IDEA_XHS_DAILY_CLUES_V3_20261127`、`TASK_VERSION: 3`、实际状态（`DONE` / `PARTIAL_DONE` / `BLOCKED`）、`NEXT_ACTOR: GEMINI`。
     - 如实列出：单测结果、模板初始化路径、轨道 A 输入/有效/拒绝条数及覆盖账号、轨道 B 一手源条数、定时任务核查结果、提交 SHA（如有）。
   - 仅在产出通过审查且无敏感信息时提交允许公开的文件（`sources/xhs_daily/*.json`、`OPENCODE_REPORT_*.md`），绝不提交 `data/` 或 `logs/`。
