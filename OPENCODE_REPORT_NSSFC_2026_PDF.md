# OPENCODE_REPORT_NSSFC_2026_PDF.md

TASK_ID: IDEA_NSSFC_2026_SU_SE_PDF_LINKS_V1
TASK_VERSION: 3
STATUS: DONE
NEXT_ACTOR: ChatGPT（正式立项核验 / 下一步审核）

- Source: https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm
- 执行时间：2026-11-09（本地在线，脚本 v3 本地运行成功）
- 运行命令：
  ```
  python scripts/inspect_nssfc_2026_pdf_links.py --url https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm --out-dir data/nssfc_2026_suse --max-pdfs 4
  ```

## 1. 结果总览
- 公告页 `notice_access = public_html_accessible`（公开可读，无登录/验证码/403/429/CF）。
- 4 份 PDF 附件**全部下载成功**（白名单已由 ChatGPT 加 `download.people.com.cn` 放行，v3）。
- 文本型标准表格（非扫描件），`pdfplumber` 逐表提取，**无错误**。

| 类别 | PDF URL | 页数 | 提取行数 | 下载大小 | 状态 |
|------|---------|------|---------|---------|------|
| 重点 | https://download.people.com.cn/yunying2/twentyfive17914600301.pdf | 18 | 439 | 471,346 B | 已下载并解析 |
| 一般 | https://download.people.com.cn/yunying2/twentyfive17914600601.pdf | 109 | 2657 | 1,001,502 B | 已下载并解析 |
| 青年 | https://download.people.com.cn/yunying2/twentyfive17914600921.pdf | 95 | 2293 | 1,080,730 B | 已下载并解析 |
| 西部 | https://download.people.com.cn/yunying2/twentyfive17914601111.pdf | 23 | 542 | 519,733 B | 已下载并解析 |
| **合计** | | | **5931** | | |

## 2. 抽查与质量核验（按任务步骤 3，未使用 OCR）
- 每类首页与末页表头一致：`序号 | 涉及学科 | 课题名称 | 负责人 | 依托单位`；页码脚注 `第 N 页 共 N 页` 标准。
- **逐项交叉核对**：每类随机抽 10 项（共 40 项），以 PDF 同页 `extract_tables()` 单元格逐一核对「课题名称+负责人+依托单位」→ **40/40 全部匹配**。提取准确。
- 字段完整性（5931 行）：`project_title`、`principal_investigator`、`organization` 空值均为 **0**。
- **`project_id` 全为空（5931/5931）——属正确结果**：拟立项公示名单**无「编号/批准号」列**（仅序号/学科/名称/负责人/单位），正式立项编号由全国社科办在批复后授予。脚本未误把「序号」当批准号。

## 3. 状态口径（任务步骤 4）
- 2026-10-10 高校转发的附件**只能记为拟立项公示**：CSV `project_status = proposed_publicity_not_formal_award`，`evidence_level = participating_university_forwarding_original_list`，`review_state = pending_official_confirmation_and_spotcheck`。
- 未对照到全国哲学社会科学工作办公室 2026 年度正式批复公告；**未**按正式立项写入。正式立项核验与去重属 ChatGPT/总控后续步骤。
- 候选 CSV `data/nssfc_2026_suse/nssfc_2026_proposed_candidates.csv`（5931 行，utf-8-sig）**未与任何正式立项库合并**（任务步骤 5）。

## 4. 合规与本地保存
- 全程未绕过登录/验证码/robots/403/429/Cloudflare；未用代理或私有接口；仅访问 SUSE 公告 + `download.people.com.cn`（已核验合法官方域，无 robots 限制，`200/application/pdf`）。
- PDF 原文与候选 CSV 仅存项目内 `data/nssfc_2026_suse/`（已 gitignore，**未提交公开仓库**）。
- 输出：`data/nssfc_2026_suse/link_probe_report.json`（已生成，含 4 直链、下载份数、页数、提取行数）。

## 5. 下一步
- 交 ChatGPT 审核 5931 条拟立项候选；如需，由 ChatGPT 对照全国社科办正式公告按项目编号/题目+负责人去重并升级状态；正式立项后另行合并，不做 OCR、不臆造编号。
