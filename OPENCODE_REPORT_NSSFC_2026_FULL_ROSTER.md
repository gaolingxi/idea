TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 1
STATUS: FAILED
NEXT_ACTOR: ChatGPT（修复审计脚本 header_map，重发）

# 国社科2026年度项目公示名册完整性专项审核

## 结论：脚本头匹配缺陷，未产出公开 CSV
- 目标：重建 6065 行（重点444/一般2705/青年2350/西部566），含 134 条「题目略」。
- 实际：`audit_nssfc_2026_full_proposed.py` 对**四类全部提取 0 行**，在质量闸门第 1 道即报错：
  `ValueError: key: PDF table has 0 rows but original announcement has 444; NOT PUBLISHING`
  （general/young/western 同因，未到达）。
- **未生成** `public_metadata/national_socsc_2026_annual_proposed.csv`，`reports/nssfc_2026_annual_proposed_audit.json` 未写（脚本在闸门处 raise，不落盘）。无假入库。

## 根因（精确诊断，可复现）
- 4 份本地 PDF 的表格表头（实测每份首页，全部一致）：
  `序号 | 涉及学科 | 课题名称 | 申请人 | 依托单位`
- `scripts/audit_nssfc_2026_full_proposed.py` 的 `header_map()` 中 `keys["person"] = ("负责人", "主持人")`，
  **未包含「申请人」**（U+7533 U+8BF7 U+4EBA）。
- `match_col` 对「申请人」既 `s != "负责人"/"主持人"`，也不含这些词 → person 列为 None →
  `all(cols[k] is not None ...)` 不满足 → `header_map` 返回 `(None, None)` → `extract()` 的 `cols is None` → 0 行。
- 对照：v3 脚本 `scripts/inspect_nssfc_2026_pdf_links.py` 的 `HEADER_PI = re.compile(r"(?:负责人|申请人|主持人)")` **含申请人**，
  故 v3 能正确提取 5931 条（person 列全部正常）。审计脚本漏了申请人这一项。

## 修复建议（由 ChatGPT 执行，OpenCode 不改代码）
- 将 `header_map()` 的 `keys["person"]` 改为 `("负责人", "申请人", "主持人")`（或正则 `(?:负责人|申请人|主持人)`）。
- 其余列（序号/涉及学科/课题名称/依托单位）匹配均正常，无需改动；预期 134 条「题目略」行（重点5/一般48/青年57/西部24）由 `is_omitted` 逻辑保留，`title_is_public=no`。

## 本地状态
- 4 份 PDF 原样保留于 `data/nssfc_2026_suse/`（未改动、未入库、gitignore）。
- 本地数据与脚本均未绕过任何访问限制；未提交任何 data/ 内容。
- 修复后重跑：`python scripts/audit_nssfc_2026_full_proposed.py --input-dir data/nssfc_2026_suse --output public_metadata/national_socsc_2026_annual_proposed.csv --audit reports/nssfc_2026_annual_proposed_audit.json`
