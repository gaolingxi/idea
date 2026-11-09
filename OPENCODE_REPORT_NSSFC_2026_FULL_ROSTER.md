TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 2
STATUS: FAILED
NEXT_ACTOR: ChatGPT（修复比较闸门的类别标签归一化，重发）

# 国社科2026年度项目公示名册完整性专项审核（v2）

## 结论：第 3 道质量闸门类别标签不一致，未产出公开 CSV
- 进展：v2 已修复 `申请人` 表头 → `header_map` 正常，四类提取分别命中 444/2705/2350/566（=6065），
  公开题目 5931、题目略 134 → 闸门 1、2 **通过**。
- **闸门 3**（前版 5931 条逐条一致）失败：
  `ValueError: Mismatch against previous 5931 project candidates; ... NOT PUBLISHING`。
- **未生成** `public_metadata/national_socsc_2026_annual_proposed.csv` 与 `reports/nssfc_2026_annual_proposed_audit.json`（脚本在闸门处 raise 不落盘）。无假入库。

## 根因（精确诊断，可复现）
- 比较闸门（`main()` 内 `new` 集合）用 `r["category"]`，其值为**英文键** `key/general/young/western`（来自 `PDFS` dict）。
- 前版 `data/nssfc_2026_suse/nssfc_2026_proposed_candidates.csv` 的 `project_category` 为**中文标签** `重点/一般/青年/西部`（来自 v3 `CATEGORIES`）。
- 二者类别标签不同 → `new != previous` 恒为真，即使内容完全一致。
- **内容实际完全一致**：忽略类别后按 `(title, person, unit)` 比较，5931 vs 5931，**EXTRA=0 / MISSING=0**（本机实测）。
- 故这是纯类别标签归一化缺陷，非内容差异。

## 修复建议（由 ChatGPT 执行，OpenCode 不改代码）
- 方案A（最小）：`main()` 比较时把 `r["category"]` 映射为中文标签（`key→重点, general→一般, young→青年, western→西部`）再与 `previous` 比较；或
- 方案B：读取 v3 CSV 时把 `project_category` 归一化为英文键再比较；或
- 方案C：闸门 3 只比较 `(title, person, unit)`（类别已由闸门 1 分四类行数严格保证），最稳。
- 其余逻辑（行数、序号连续、134 略、内容一致）均已验证正确，无需改动。

## 本地状态
- 4 份 PDF 原样保留于 `data/nssfc_2026_suse/`（未改动、未入库、gitignore）。
- 修复后重跑：`python scripts/audit_nssfc_2026_full_proposed.py --input-dir data/nssfc_2026_suse --output public_metadata/national_socsc_2026_annual_proposed.csv --audit reports/nssfc_2026_annual_proposed_audit.json`
