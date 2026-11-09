TASK_ID: IDEA_NSFC_PROJECT_LEVEL_SEED_V1_20261109
TASK_VERSION: 2
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_NSFC_SEED.md;scripts/collect_nsfc_awards_from_universities.py;sources/nsfc_award_source_registry.json;requirements-site-crawler.txt;AGENTS.md

# 当前任务：国家自然科学基金真实项目名称首批采集

国社科2026公示6065条已完成并冻结，不再正式批复核验。国自然项目级资料原先为0条，第一轮只处理4份已定位的大学公开获资助表格，并核查基金委公开查询来源。子任务：OPENCODE_TASK_NSFC_SEED.md。

## 版本2：修复首轮BLOCKED问题
首轮已执行，国自然项目入库0条（南开及湖南师大两个年度因 `requests` 在无charset的UTF-8网页中返回ISO-8859-1导致乱码；华中科技大学经济学院是HTTPS SSL连接失败，必须保留真实阻塞，绝不关掉证书验证）。ChatGPT现已更新脚本：在无明确编码或ISO-8859-1回退时先严格按UTF-8解析，失败才让BeautifulSoup探测其他编码；补充中文表头回归测试。请只重跑这一批，成功提取公开清单、去重、抽查后回写结果，并检查基金委公开查询站点的合规可用性。不要把高校局部名单当全国完整项目库。保留v1 BLOCKED审计记录。
