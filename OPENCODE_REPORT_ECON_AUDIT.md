TASK_ID: IDEA_ECON_DATA_AUDIT_V1_20261127
TASK_VERSION: 1
STATUS: DONE
NEXT_ACTOR: GEMINI

# 经济学原始资料层质量排查报告（只读排查，未修改任何数据文件或脚本）

## 一、同步与自检
- 已同步 `origin/main`（HEAD 1517c52），核对 `AGENTS.md`、`STAGE_PLAN.md` 一致。
- 本报告仅排查定位，未改动 `scripts/`、`sources/`、`public_metadata/`、`data/`、`logs/` 任何文件。

## 二、日期截断 Bug 定位（步骤 2）

### 根因：日分组 `0?[1-9]` 排在 `[12]\d`、`3[01]` 之前，`search()` 无尾锚致两位日被截为十位数字。
- **文件/行号**：
  - `scripts/crawl_official_sites.py` **L27**：`DATE = re.compile(r"(?<!\d)(20(?:2[4-9]|3\d))[-./年](0?[1-9]|1[0-2])[-./月](0?[1-9]|[12]\d|3[01])日?")` —— 日分组 `(0?[1-9]|[12]\d|3[01])` 首位 `0?[1-9]`。
  - `scripts/grant_hourly_monitor.py` **L23**：`DATE_RE=re.compile(r"20(?:24|25|26)[年./-]\s*(?:0?[1-9]|1[0-2])[年./-]\s*(?:0?[1-9]|[12]\d|3[01])")` —— 日分组 `(?:0?[1-9]|[12]\d|3[01])` 首位 `0?[1-9]`。
- **机制**：对两位日 10-31，`0?[1-9]` 只匹配**首位（十位）数字**（10→1、28→2、30→3）；因是 `re.search()`（非 fullmatch）且日分组后无 `(?!\d)` 前瞻，个位被静默丢弃，正则整体成功但日期错误。
- **实证**（本地运行验证）：
  - `crawl.date_from('2026/10/30') = '2026-10-03'`；`crawl.date_from('2026年11月10日') = '2026-11-01'`；`crawl.date_from('2025/07/28') = '2025-07-02'`（对应任务中的 `2025/0728 -> 2025-07-02`，实际输入为 `2025/07/28`）。
  - `grant DATE_RE` 同截断：`'2026/10/3'`、`'2026年11月1'`、`'2025/07/2'`。
  - 日分组演示：`10→'1'`、`15→'1'`、`19→'1'`、`20→'2'`、`28→'2'`、`30→'3'`、`31→'3'`；`01→'01'`、`09→'09'` 正常。
  - 注：`'2025/0728'`（7 位无分隔）两正则**均不匹配**（返回 `''`/None），非产生错误日期而是无日期。
- **修复建议**：将日分组重排为最长优先 `(?:[12]\d|3[01]|0?[1-9])`，并加 `(?!\d)` 前瞻（`...日?(?!\d)`）。已验证重排后 `10/15/19/20/28/30/31` 全部正确捕获。

## 三、24 个月过滤缺口定位（步骤 3）

### 根因：`scripts/grant_hourly_monitor.py` L140 的 `or` 分支无条件保留缺日期行。
- **L140**：`if GRANT.search(row.get("notice_title","")) and (not row.get("publication_date") or row["publication_date"]>=start):`
- **L151 注释**：「Undated entries are registered as candidate links, not counted in a verified rolling window」。
- **机制**：`not row.get("publication_date")` 短路**保留所有无发布日期行**，绕过 24 个月窗口（`start=today-2年`）。故无日期旧公告无法被窗口过滤剔除，持续混入。
- **实际数据**（`public_metadata/grant_source_notices.csv`，173 行）：**缺日期 87 条** + 窗口内（≥2024-11-27）86 条 + 有效 ISO 旧日期（<2024-11-27）0 条。
  - 任务表述「86 条缺日期」，本地实测 87 条（快照可能因重跑增 1 条；以实际为准）。
  - 「2016-2023 旧公告」即这 87 条**缺日期**行，其标题含 2016-2023 年份（标题年份提及：2019:7、2020:5、2022:6、2018:4、2017:5、2021:5、2023:5、2016:1）——因无 `publication_date`，窗口过滤无法排除，全部作为候选链接保留。
- **修复建议**：将窗口判定改为「必须有窗口内日期」：`pub = row.get("publication_date","")`，仅当 `pub and pub>=start` 才进入已验证窗口集；缺日期行单独标记为 `undated_unverified_candidate` 通道，不静默混入公告集。

## 四、会议论文与部委政策 0 条原因（步骤 4，仅代码级定位）

`official_source_pages.csv` 由 **`scripts/merge_public_index.py`** 产出；其 **L36**：`if not pub or pub<start or pub>now or not title: continue`（过滤缺发布日期/窗口外/无标题行）。

| 来源 | 模式 | 判定（本地单页探测，尊重 robots） | 0 条根因 |
|------|------|--------------------------------|---------|
| `conference_cea_2025_attachment` | attachment | xlsx 可下载（`application/vnd.openxmlformats-officedoc`），非 HTML | **设计**：`crawl_official_sites.py` L300-303 写附件库（非 `documents` 表）；191 篇论文在 xlsx 中另行提取且**未验证**（merge L51）。 |
| `conference_cfrc_2025` | detail | HTML 200，title="2025 China Financial Research Conference"，`extract_dates` 得 **pub=""** | 种子页被 upsert，但 **pub 为空** → merge L36 `not pub` 过滤 → 0。 |
| `conference_cfrc_2026` | detail | HTML 200，title="China Financial Research Conference"，pub=""，60 个 talk 链接 | 同上（程序页无发布日期，talk 标题非带日期文档）。 |
| `policy_ndrc` | listing | **`PermissionError: robots access blocked: 403`**（robots.txt 403） | robots/403 访问限制，爬虫依法拒绝 → 0（真实阻塞）。 |
| `policy_miit` | listing | HTML 200（title="文件发布"），但可检测链接为**短导航标签**（首页/政务公开/政策文件/通知/公告，2-4 字） | `crawl_official_sites.py` L357 `8<=len(label)<=240` 不满足（标签过短）；真实通知文章链接疑 JS 动态加载 → **0 合格 article 链接** → 0。 |

- 未发起大规模爬取；以上均为逐源单页代码级探测（用 `SiteFetcher`，遵守 robots）。
- **修复方向**：cfrc 需为程序页补「会议日期/公告日期」来源或对无日期 detail 页标记未验证；miit 需确认通知链接是否 JS 加载、改用含长标题的列表容器或放宽标签长度（需配合主题词防误捕）；ndrc 需确认 robots 403 是否为 UA 白名单（换合规 UA）或标记不可用；cea attachment 属设计，其 xlsx 论文需单独验证后入公开元数据。

## 五、合规说明
- 全程只读；未修改任何脚本/数据；未绕过 robots/403/429/验证码/登录；未使用代理或私有接口；未提交 `data/`、`logs/`、正文、凭证。
- 本报告为代码级定位，供 Gemini 审核并修订脚本。
