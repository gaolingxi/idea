TASK_ID: IDEA_XHS_DAILY_CLUES_V3_20261127
TASK_VERSION: 3
STATUS: BLOCKED_WAITING_AUTHORIZED_INPUT
NEXT_ACTOR: GEMINI

# 每日小红书经管选题线索框架 v3｜本地 Orca OpenCode 执行回执

## 1. 环境与代码自检
- 工作树干净，已同步 `origin/main`（HEAD 26332c5）。
- 单元测试：`python -m unittest discover -s tests -p "test_xhs*.py" -v` → **9/9 通过**（`test_xhs.py` 5 项：test_date / test_meta / test_reject_missing_permission / test_reject_untrusted_url / test_sqlite_dedup；`test_xhs_daily_clues.py` 4 项：test_build_approved_clues_and_snapshot / test_build_public_leads_rejects_xhs_url_as_primary / test_init_templates_creates_both_files / test_load_registry_has_four_active_accounts）。

## 2. 本地模板初始化（仅本地 `data/xhs/`，未提交 Git）
- `data/xhs/daily_approved_clues.template.csv`（135 B）已生成，表头：`account,published_at,source_url,concept,topic_category,primary_source_url,allow_collect,allow_public_share,authorization_reference`
- `data/xhs/public_clue_leads.template.csv`（147 B）已生成，表头：`discovered_date,topic_category,concept,primary_source_type,primary_source_title,primary_source_url,primary_published_date,related_account_hint`

## 3. 轨道 A：获准小红书线索入库（主轨）
- 本地 `data/xhs/daily_approved_clues.csv` **不存在** → `BLOCKED_WAITING_AUTHORIZED_INPUT`。
- 输入 0 / 有效 0 / 拒绝 0；覆盖账号：无；覆盖日期：无。
- 未抓取平台、未生成 `sources/xhs_daily/latest.json`、未覆盖任何旧快照（不存在）。

## 4. 轨道 B：公开索引回溯一手源（补充轨）
- 本地 `data/xhs/public_clue_leads.csv` **不存在** → 一手源条数 0。
- 未生成 `sources/xhs_daily/verified_public_leads.json`。

## 5. 每日定时触发状态核查
- Windows 计划任务 `idea-OpenCode-10min` **存在且已启用**，每 10 分钟轮询（`wscript //B hidden_runner.vbs`）。
- 上次运行：2026/11/27 20:29:18，上次结果 0；下次运行：2026/11/27 20:39:17。开始日期 2026/11/9。
- 未新建重复任务。

## 6. 提交与交接
- 无新增公开 JSON（latest.json / verified_public_leads.json 未生成，无敏感或可提交数据）。
- 提交内容：`OPENCODE_REPORT_XHS_DAILY.md` + `OPENCODE_REPORT_AUTORUN.md`。`data/`、`logs/` 未提交。
- `NEXT_ACTOR: GEMINI`。

## 合规说明
- 未绕过登录墙/验证码/403/429/robots/服务协议；未自动登录、未提取 Cookie、未调用私有接口、未模拟浏览器规避限制。
- 未提交 `data/`、`logs/`、笔记正文、标题全文、截图、评论、个人隐私或授权凭证；无伪造记录或虚报条数。
