TASK_ID: IDEA_NSFC_PROJECT_LEVEL_SEED_V1_20261109
TASK_VERSION: 2
STATUS: PARTIAL_DONE
NEXT_ACTOR: ChatGPT（审核，规划下一批来源）

# 国自然2025—2026年逐项资助项目首批采集报告（v2）

## 结果：46 条项目级记录入库（3 源成功，1 源 SSL 阻塞）
- 运行：`python scripts/collect_nsfc_awards_from_universities.py --registry sources/nsfc_award_source_registry.json --output public_metadata/nsfc_awards_2025_2026_partial.csv --audit reports/nsfc_awards_2025_2026_seed_audit.json`
- `status=PARTIAL_PROJECT_LEVEL_SEED_COLLECTED`，`new_or_verified_approval_numbers=46`，`index_total_unique_approval_numbers=46`。

| 来源 | 年份 | 成功数 | 状态 |
|------|------|-------|------|
| 南开大学经济学院 | 2026 | 11 | collected |
| 湖南师范大学物电学院 | 2026 | 23 | collected |
| 湖南师范大学物电学院 | 2025 | 12 | collected |
| 华中科技大学经济学院 | 2026 | 0 | SSL 阻塞（证书/连接，非脚本缺陷） |
| **合计** | | **46** | |

- 2025 年 12 条 / 2026 年 34 条；管理科学/经济方向 = 南开 11 条；其他学科（物电）= 湖南师大 35 条。
- 批准号全部唯一（46/46），无重复、无冲突。

## 抽查（任务步骤 5）
- **46/46 逐条与源页面一致**：每行「批准号 + 项目名称 + 负责人」均能在对应公开页面文本中定位（南开 11/11、湖南师大26 23/23、湖南师大25 12/12）。
- 未发现错别字/重复/缺项；`approval_number` 全为 8 位（`\d{8}`）。
- `source_level=university_published_award_list`，`collection_scope=partial_institution_records_not_nationwide`（未改全国覆盖）。

## 官方查询平台核验（任务步骤 6，正常页面浏览，未逆向 API）
- `https://kd.nsfc.cn/` 正常加载（HTTP 200，浏览器渲染 = 「国家自然科学基金大数据知识管理服务门户」）。
- **公众免登录可用**：「数据查询」搜索框（请输入项目或成果关键词）+「信息检索」菜单 + 科研人员/项目详情页（`/finalDetails?id=` 公开可点）；公开基础数据（资助项目数 738,916 等）。
- 存在「登录」（个人中心/更全数据），且「本平台提供的数据仅供参考」声明。
- 未验证全量逐条导出；不建议批量抓取门户（可能触发 429/验证码，且超出本批范围）。下一批如需，建议单独评估合规导出方式。

## 提交内容
- `public_metadata/nsfc_awards_2025_2026_partial.csv`（46 行）
- `reports/nsfc_awards_2025_2026_seed_audit.json`
- 本报告（`data/`、`logs/` 及原页面未上传；华科源 SSL 阻塞已记录）。

## 停止说明
- 本批达到「至少一个明确项目级公开来源成功提取且逐项抽查通过」，按实际成功数报告 **PARTIAL_DONE**。
- 下一批来源与扩量由 ChatGPT 审核；国社科 6065 条冻结不动；未宣称全国覆盖，未称基金委逐项认证（`review_state=pending_crosscheck_with_NSFC_public_record`）。
