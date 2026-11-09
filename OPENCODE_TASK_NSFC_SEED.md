# OpenCode专项任务｜2025—2026国家自然科学基金项目级名单采集（首批）

TASK_ID: IDEA_NSFC_PROJECT_LEVEL_SEED_V1_20261109
TASK_VERSION: 2
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES

## 目标与已有事实
国社科2026公示6065条已DONE、冻结，不再继续国社科任务。本次只做**国家自然科学基金（国自然）**，以管理科学部/经济金融类为先，同时测试公开的其他学科与2025年资料。
基金委2026年8月26日公布的69563项为资助总数，**不是69563条项目级记录**。原则：取得明确项目名称、项目批准号、负责人、来源的真实记录才计数。

## 执行（ChatGPT写代码；OpenCode只运行）
1. 只在`gaolingxi/idea`本地仓库执行，不到其他项目文件夹。审阅`AGENTS.md`、`sources/nsfc_award_source_registry.json`和本任务。
2. 运行：
```bash
python -m pip install -r requirements-site-crawler.txt
python -m py_compile scripts/collect_nsfc_awards_from_universities.py
python scripts/collect_nsfc_awards_from_universities.py --registry sources/nsfc_award_source_registry.json --output public_metadata/nsfc_awards_2025_2026_partial.csv --audit reports/nsfc_awards_2025_2026_seed_audit.json
```
3. 清点每个站点：官方大学子域是否能合法访问、页面是否提供含「项目批准号、负责人、项目名称」的结构化表格；按项目批准号去重，冲突必须报告，不能随意覆盖。
4. 首批已定位的四份来源：华中科技大学经济学院2026、南开大学经济学院2026、湖南师范大学物电学院2026及2025。这是**局部高校公开名单，不是全国完整名单**。输出CSV中的`source_level=university_published_award_list`和`collection_scope=partial_institution_records_not_nationwide`不允许改成全国覆盖。
5. 用每个来源的实际页面至少抽查3条「批准号+题目+负责人」是否一致，记录错别字、重复和缺项。只允许提交确实来自公开页面且字段可核查的书目元数据。此批先保留`review_state=pending_crosscheck_with_NSFC_public_record`，不能称已由基金委逐项认证。
6. **单独核验官方公开项目查询来源**：官方FAQ https://www.nsfc.gov.cn/p1/2961/2962/3648/cx.html 提到 https://kd.nsfc.cn/；检查公众无需登录能否查项目/批号，是否提供合规可用的逐条导出方式。只作人工/正常页面查询，未授权、需账号、验证码、robots拒绝、429、Cloudflare等立即停止，不抓私有接口，不使用第三方镜像当官方。
7. `public_metadata/nsfc_awards_2025_2026_partial.csv` 和 `reports/nsfc_awards_2025_2026_seed_audit.json` 只有确有通过核实的公开书目项才提交。数据、访问日志、原PDF只存本项目`data/`、`logs/`，不上传。
8. 回写`OPENCODE_REPORT_NSFC_SEED.md`及`OPENCODE_REPORT_AUTORUN.md`，包括收集总数、2025/2026分别多少、管理科学方向多少、每个来源成功/阻塞原因、查询平台可用性、下一批建议。成功后停止该批，交ChatGPT审核。
9. 国社科线已冻结：**不再修改**国社科任务/报告/6065条数据，也不启动国社科正式核验。

## 停止条件
至少一个明确项目级公开来源成功提取且逐项抽查后，按实际成功数报告 PARTIAL_DONE；如果无来源成功，状态BLOCKED，并给出具体失败原因。**不能以工程测试通过代替项目入库。**

## 版本2：修复首轮BLOCKED问题
首轮已执行，国自然项目入库0条（南开及湖南师大两个年度因 `requests` 在无charset的UTF-8网页中返回ISO-8859-1导致乱码；华中科技大学经济学院是HTTPS SSL连接失败，必须保留真实阻塞，绝不关掉证书验证）。ChatGPT现已更新脚本：在无明确编码或ISO-8859-1回退时先严格按UTF-8解析，失败才让BeautifulSoup探测其他编码；补充中文表头回归测试。请只重跑这一批，成功提取公开清单、去重、抽查后回写结果，并检查基金委公开查询站点的合规可用性。不要把高校局部名单当全国完整项目库。保留v1 BLOCKED审计记录。
