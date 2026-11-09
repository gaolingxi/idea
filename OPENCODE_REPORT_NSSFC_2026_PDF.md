# OPENCODE_REPORT_NSSFC_2026_PDF.md

TASK_ID: IDEA_NSSFC_2026_SU_SE_PDF_LINKS_V1
STATUS: BLOCKED
NEXT_ACTOR: ChatGPT（脚本修订，白名单加域）

- Source: https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm
- 执行时间：2026-11-09（本地在线，脚本本地运行成功）
- 单元测试 / 依赖：`python -m py_compile` 通过；`requirements-site-crawler.txt` 已满足（requests/bs4/pdfplumber 均在）
- 运行命令：
  ```
  python scripts/inspect_nssfc_2026_pdf_links.py --url https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm --out-dir data/nssfc_2026_suse --max-pdfs 4
  ```

## 1. 公告页访问结果
- `notice_access = public_html_accessible`：公告 HTML **公开可读**，无需登录/验证码，无 401/403/429/Cloudflare。
- 页面内发现 **4 个 PDF 附件直链**（重点/一般/青年/西部 各 1），全部为 `https://download.people.com.cn/yunying2/twentyfive17....pdf`。

## 2. PDF 直链与白名单状态
| 类别 | PDF URL | 域内白名单 | 脚本结果 |
|------|---------|-----------|---------|
| 重点 | https://download.people.com.cn/yunying2/twentyfive17914600301.pdf | 否 | external_domain_requires_separate_official_verification |
| 一般 | https://download.people.com.cn/yunying2/twentyfive17914600601.pdf | 否 | 同上 |
| 青年 | https://download.people.com.cn/yunying2/twentyfive17914600921.pdf | 否 | 同上 |
| 西部 | https://download.people.com.cn/yunying2/twentyfive17914601111.pdf | 否 | 同上 |

脚本 `ALLOWED_HOSTS = ["suse.edu.cn"]`，4 份 PDF 全部托管在 `download.people.com.cn`（人民网下载域），**不在白名单** → 按安全规则未下载。`downloaded_pdfs = 0`、`extracted_candidate_rows = 0`。

## 3. 跨域承载域核查（本机实测，仅验证，未下载正文）
- `https://download.people.com.cn/robots.txt` → **HTTP 404**（无 robots 限制，按约定无明确禁止）。
- 对重点类 PDF 做 HEAD：`HTTP 200`，`Content-Type: application/pdf`，`Content-Length = 471346`（约 460 KB），公开免登录可下载。
- 结论：`download.people.com.cn` 属**合法公开官方承载域**（人民日报社/人民网官方下载服务器），4 份 PDF 均为公开、无权限门槛的官方附件。符合任务安全条款"核查确属合法公开官方承载域名"。

## 4. 为何未下载 / 下一步（需 ChatGPT 决定）
- 任务明令 `不改代码；如脚本能力不足，回报具体故障，由 ChatGPT 迭代脚本`；`AGENTS.md` 明确 `ChatGPT 负责脚本修订`。
- 白名单 `ALLOWED_HOSTS` 增加 `"people.com.cn"` 属**脚本修订**，**OpenCode 不擅自修改**。
- 建议：ChatGPT 将 `scripts/inspect_nssfc_2026_pdf_links.py` 的 `ALLOWED_HOSTS` 增加 `"people.com.cn"` 后重新下发（或将 4 个直链写死为允许）。我已核验该域合法，可直接放行。
- 放行后即可在本地完整执行：下载 4 份 PDF → `pdfplumber` 逐表提取题目/编号/负责人/单位 → 抽查每类首页末页+10 项 → 回写候选 CSV。

## 5. 合规与状态口径
- 全程未绕过登录/验证码/robots/403/429，未使用代理或私有接口；未抓取任何第三方域内容。
- 项目状态口径：2026-10-10 高校转发名单仅为**拟立项公示**（`proposed_publicity_not_formal_award`），**不得**记为正式立项，除非全国社科办另行正式公告。
- 本地未生成候选 CSV（0 行），未与任何正式立项库合并。
- 报告状态：**BLOCKED**（跨域白名单未放行，待 ChatGPT 脚本修订），非科研终点。

- 输出报告：`data/nssfc_2026_suse/link_probe_report.json`（已生成，含 4 直链与 blocked 明细）
