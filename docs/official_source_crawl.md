# 官方网站站内采集（原始资料层）

## 为什么要站内采集
此前按搜索结果逐条发现，遗漏了2025-2026年已经公开的整份论文/项目名单。现改为“**固定官方栏目—历史页—详情页—附件**”。

## 来源
18个经公开来源验证的入口：`sources/site_registry.json`。重点：国家社科基金年度/重大项目、国家自然科学基金管理科学部、国家统计局及中国统计学会、2025/2026中国经济学年会、2025/2026中国金融学术年会、2026重庆数量经济学会会议、发改委/财政部/商务部/工信部政策栏。

## 本地安装及小规模测试
```bash
python -m pip install -r requirements-site-crawler.txt
python -m unittest discover -s tests -p "test_site_crawler.py" -v
python scripts/crawl_official_sites.py --source-id project_stats_2026 --max-pages 1 --max-details 5 --attachments
python scripts/crawl_official_sites.py --source-id policy_mof --max-pages 4 --max-details 30
```

## 关键数据质量规则
- `documents` 是网站**公告/原文页**，不是逐条科研立项或单篇论文。只有附件逐条提取且复核后，才能计入单项总数。
- `attachments` 储存合法可访问的PDF等附件及提取状态；`extracted_candidates` 中的表格行是“待核实”，不等于正式入库。
- `formal_or_reported_award`、`proposed`、`call_or_guidance` 不可合并为同一状态。
- 政策发布日期、成文日期、实施条款分开记录；日期无法核实则不计入滚动24个月已验证条目。
- 采集速率受限，严格遵守robots和站点条款。401/403/429直接停止对应来源，不做验证码/登录/代理绕过。
- `data/`、`logs/` 仅保存在本项目本地文件夹，不提交公开GitHub。中国统计学会站点声明不得转载，原始内容仅限许可范围内处理。
- 首轮先测试可行性，再分批历史回补。脚本当前不保证解析所有PDF表格和Excel附件，不得谎报完整率。

## 分阶段停止条件
1. 首先每站采集并生成覆盖与阻塞报告；
2. 然后针对2025/2026的官方立项PDF、年会xlsx/pdf逐一设计**确定性表头解析**，与公告状态核对；
3. 仅在验证准确率后扩展到整站翻页。每小时任务仅处理新增，历史缺口另做一次回补。
