TASK_ID: IDEA_NSFC_PROJECT_LEVEL_SEED_V1_20261109
TASK_VERSION: 1
STATUS: BLOCKED
NEXT_ACTOR: ChatGPT（修复脚本编码处理；核验华科 SSL）

# 国自然2025—2026年逐项资助项目首批采集报告

## 结论：0 条入库，BLOCKED。3 源为脚本编码缺陷，1 源为 SSL 阻塞。
- 运行：`python scripts/collect_nsfc_awards_from_universities.py --registry sources/nsfc_award_source_registry.json --output public_metadata/nsfc_awards_2025_2026_partial.csv --audit reports/nsfc_awards_2025_2026_seed_audit.json`
- 结果：`status=BLOCKED_NO_NEW_PROJECT_LEVEL_SOURCES`，`new_or_verified_approval_numbers=0`。
- **未生成** `public_metadata/nsfc_awards_2025_2026_partial.csv`（无假入库）。审计 JSON 已写 `reports/nsfc_awards_2025_2026_seed_audit.json`（含各源失败原因）。

## 逐源诊断（本机实测）

### 1. 南开大学经济学院 2026（economics.nankai.edu.cn）— 脚本编码缺陷
- 页面 **HTTP 200 / text/html**，真实含结构化立项表（表 0：列头 `项目批准号 | 负责人 | 项目名称 | 项目类别`；数据行如 `72673088 丁华、72673090 宋泽`，均为面上项目）。
- **根因**：页面为 UTF-8 但响应头 `Content-Type: text/html` **无 charset**；`requests` 默认 `response.encoding = ISO-8859-1`。脚本第 120 行 `BeautifulSoup(raw,"html.parser",from_encoding=encoding)` 直接用它 → 中文全部乱码 → `find_header` 匹配失败 → 报 `No structured NSFC awards with approval numbers found`。
- **验证**：用 `response.apparent_encoding`（utf-8）解码 → `项目名称` 正常出现，表头可匹配。
- **修复建议**：`from_encoding` 对 iso-8859-1/latin-1/none 传 `None`（自动探测），或改用 `apparent_encoding`；与 `scripts/crawl_official_sites.py` 的 `html_data()`（iso-8859-1→None）保持一致。

### 2/3. 湖南师范大学物电学院 2026 / 2025（wdy.hunnu.edu.cn）— 同编码缺陷
- 两页均 **HTTP 200 / text/html**，`encoding=ISO-8859-1`、`apparent=UTF-8-SIG`（无 charset 头）。同 1 的编码缺陷 → 0 行。修复同上。

### 4. 华中科技大学经济学院 2026（eco.hust.edu.cn）— SSL 阻塞（非脚本缺陷）
- 脚本在 `robots.txt` 抓取即失败；本机实测主 URL 亦 `SSLError: HTTPSConnectionPool(host='eco.hust.edu.cn', port=443): Max retries exceeded`（证书/连接层）。
- 属真实源级网络/证书阻塞，无法合法绕过。需 ChatGPT 判断是否换源、或该子域需特殊 TLS/证书配置，或标记为不可用。

## 其他
- 官方查询平台 `https://kd.nsfc.cn/` 按任务步骤 6 属独立核验项；本批未执行（先阻塞于来源提取）。建议 ChatGPT 在编码修复后一并安排查询平台可用性核验。
- 全程未绕过 robots/验证码/403/429/Cloudflare；未用代理/私有接口；`data/`、`logs/` 未上传。
- 国社科 6065 条**冻结不动**。

## 下一步
ChatGPT 修复 `collect_nsfc_awards_from_universities.py` 编码处理（iso-8859-1→None）后重发；华科源若 SSL 无法解决则标记阻塞。重跑命令同上。
