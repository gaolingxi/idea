TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 3
STATUS: DONE
NEXT_ACTOR: ChatGPT（正式批复核验 / 下一步审核）

# 国社科2026年度项目公示名册完整性专项审核（v3）

## 结论：全部质量闸门通过，6065 行公示名册已入库
- 脚本 `scripts/audit_nssfc_2026_full_proposed.py` 本地运行成功，输出：
  - `public_metadata/national_socsc_2026_annual_proposed.csv`（6065 行，utf-8-sig）
  - `reports/nssfc_2026_annual_proposed_audit.json`（审计明细）

## 关键指标（全部核对通过）
- **总数 6065** = 重点 444 + 一般 2705 + 青年 2350 + 西部 566（分四类逐项命中）。
- **公开题目 5931**（`title_is_public=yes`），**题目略 134**（`title_is_public=no`，`title` 留空，`original_title_cell` 保留原字「略」等）：重点5 / 一般48 / 青年57 / 西部24。
- **前版 5931 条逐条精确匹配**：`prior_5931_candidates_exact_match=true`（类别标签已由 ChatGPT 在 v3 归一化；忽略类别时内容 `(title,person,unit)` 0 差）。
- **序号连续无断号/重复**（每类 1..N）；`project_id` 全空（名单无批准号，序号非批准号）。
- 字段完整：fund/year/award_status/category/list_sequence/discipline/title/title_is_public/original_title_cell/person/unit/project_id/source_notice/attachment_url/pdf_page/provenance/review_state。

## 数据洁净核验（任务步骤 5）
- 公开 CSV 仅含**允许公开的项目元数据**：来源公告 URL、附件 URL、PDF 页码、书目字段；不含原 PDF 文件、私人资料、Cookie/密钥。
- secret 扫描：命中 1 行为**误报**——西部类 seq 98 课题标题合法含英文词「Token」（通证/代币，区块链数字经济学术用语），非凭据/密钥。
- 未提交 `data/`、`logs/` 下任何 PDF 或原始文件（gitignore）。

## 状态口径
- 全部 6065 行 `award_status = proposed_publicity_not_formal_award`，`review_state = public_original_table_pending_final_award_confirmation`。
- **拟立项公示**，非正式立项；正式批复核验与去重由 ChatGPT 后续按项目编号/题目+负责人处理。

## 提交内容
- `public_metadata/national_socsc_2026_annual_proposed.csv`
- `reports/nssfc_2026_annual_proposed_audit.json`
- 本专项报告
（`data/`、`logs/` 及 PDF 原文不入库）
