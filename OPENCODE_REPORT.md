# OPENCODE_REPORT.md
TASK_ID: IDEA_XHS_AUTHORIZED_COLLECTION_V1_20261107
STATUS: BLOCKED

- 本地连接：online（2026-11-07 实测可达 xiaohongshu.com）
- 单元测试：passed（5/5，tests/test_xhs.py）
- 许可数据来源：已验证，**无合规来源**（证据见 logs/xhs_rights_review.md）
- 已批准来源数：0
- 实际成功采集数：0
- 24个月有效数：0
- 重复数：0
- 日期缺失数：0（未采集，无从统计）
- 拒绝原因：
  - robots.txt `User-agent: *` 为 `Disallow: /`，全站禁止通用爬虫；脚本 UA `ResearchMetadataIndexer/1.0` 属 `*` 组，任何 URL 均被 `can_fetch()` 拒绝。
  - 无平台获准数据导出（无 `data/xhs/approved_export.csv`）。
  - 无逐条许可公开页 URL（无 `data/xhs/approved_urls.csv`；模板均为占位符 `allow_collect=no`）。
  - 司法判例：未经授权抓取小红书数据已致刑事（3 人被判刑，2025-03）与民事（杭州中院终审判赔 490 万，2025-04）后果；福建高院 2026-04 典型案例确认批量抓取/搬运构成不正当竞争边界。
- 采集状态：未采集任何正文或元数据（0 条入库，SQLite 未创建数据行）
- 明确阻塞原因：平台 robots 全站禁止 + 无任何许可授权来源 + 司法/执法明确禁止未经授权抓取
- 下一步：等待平台官方数据导出或逐条书面许可的 URL 清单后方可试采；**不自动抓取、不绕过限制、不每小时轮询**。下一轮是否扩量由 ChatGPT 审核。
