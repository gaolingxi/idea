# OPENCODE_TASK_SITE_CRAWL.md
TASK_ID: IDEA_OFFICIAL_SITE_BACKFILL_V1_20261108
STATUS: READY_FOR_LOCAL_EXECUTOR
NEXT_ACTOR: OpenCode
SCOPE: policy / funded_project / conference_paper (EXCLUDES Xiaohongshu)

## 目标
**不再每小时全网关键词检索**，首先从 `sources/site_registry.json` 的21个官方来源开展站内历史采集，时间范围是运行当日往前滚动24个月。先解决完整来源和历史缺口，再进行增量。

## 执行（ChatGPT编写脚本；OpenCode仅执行）
1. 在本项目文件夹内 `python -m pip install -r requirements-site-crawler.txt`。
2. 在本项目文件夹内 `python -m unittest discover -s tests -p test_site_crawler.py -v`；如失败，不自行大范围重写，报告给ChatGPT。
3. 第一轮先跑四份国家统计局**正式立项**名单：
```bash
python scripts/crawl_official_sites.py --source-id project_stats_2025 --source-id project_stats_2026 --source-id project_stats_major_2025 --source-id project_stats_major_2026 --attachments --max-pages 1 --max-details 1
```
4. 再跑财政部历史分页和国家自然科学基金管理科学部、国家社科基金栏目：
```bash
python scripts/crawl_official_sites.py --source-id policy_mof --source-id project_nsfc_management --source-id project_nopss_major --max-pages 4 --max-details 40
```
5. 再跑中国金融学术年会及中国经济学年会入选论文公告、2025正式Excel名单：
```bash
python scripts/crawl_official_sites.py --source-id conference_cfrc_2025 --source-id conference_cfrc_2026 --source-id conference_cea_2025 --source-id conference_cea_2025_attachment --source-id conference_cea_2026 --attachments --max-pages 1 --max-details 5
```
6. 输出 `data/site_crawl/materials.sqlite`、`data/site_crawl/documents.csv`、`data/site_crawl/crawl_summary.json` 及下载附件。归档数据严格保存在本项目文件夹内 `data/`，不要推送公开GitHub。
7. 将实际成功页面数、2024-2026日期合格数、附件PDF/Excel数量、各站被拒原因填入 `OPENCODE_REPORT_SITE_CRAWL.md`。

## 质量与停止
- 不把一个公告等同于一个立项题目；逐项题目必须从正式PDF/XLSX经表头解析、人工抽样核实后另行计数。
- 征文通知、会议报道和论坛主题不能冒充入选论文名单。
- 指南 / 拟立项 / 正式立项要单独标记，不能重复计数。
- 没有成文/实施日期就留空，不估算。
- 站点有版权、robots或访问限制，则只收录允许使用的公开标题/链接；遇401/403/429/验证码停下，不绕过。
- 先检查首批结果质量，再决定是否投入每小时站内采集；OpenCode不能声称未运行的采集完成。
