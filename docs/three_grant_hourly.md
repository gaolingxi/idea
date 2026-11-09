# 每小时三级科研立项采集｜2026-11-09

## 目标与调度

- 用户要求：**国家自然科学基金（国自然）、31省级社科基金、国家社科基金（国社科）每小时定向采集**。
- GitHub Actions：`.github/workflows/hourly-three-grant-sources.yml`，UTC每小时第10分钟触发；GitHub托管Runner，**不依赖本地OpenCode开机**。受GitHub Actions排队/延迟机制影响，实际开始时间未必精确。
- 另设ChatGPT定时任务：`三级科研立项采集`，RRULE=HOURLY，发现新项目、来源补齐或重要采集失败时才报告。其执行和GitHub任务独立。
- 当前滚动24个月，按北京时间/东京时区当地日期计算，明确原始公告日期、项目年度，区分拟立项、正式立项、申报指南、结项。

## 持久数据库（公开仓库只存公开、可核查索引）
| 文件 | 内容 | 统计规则 |
| --- | --- | --- |
| `public_metadata/provincial_socsc_projects.csv` | 省社科逐项项目题目、编号、负责人、来源 | 专门统计项目题目，按省份+年度+项目编号或名称去重；目前已有2355行待抽样复核 |
| `public_metadata/grant_source_notices.csv` | 三级来源的官方公告链接、状态与来源等级 | **只是公告数量，不能当成项目数量** |
| `public_metadata/national_grant_project_candidates.csv` | 国自然/国社科正式/拟立项PDF明确表头下的逐行题目 | 仅为待逐条复核的项目，**不等于已核实正式立项数** |

## 站点与边界
- 国社科：全国哲学社会科学工作办公室年度、重大、专项工程栏目，优先正式项目结果和官方附件；不能把2026年10月的公示当正式立项。
- 国自然：国家自然科学基金委员会管理科学部和全国评审结果页面。公开官网的资助总数不是逐项项目名单；需要登录科学基金网络信息系统的资料不抓取。
- 省社科：`sources/provincial_socsc_registry.json` 的31省名单，先采可信的规划办/社科联正式名单，大学局部喜报不冒充全省完整数据。
- 必须遵守robots/访问限制，禁止代理、验证码、登录绕过和模拟非公开接口。
- 原始PDF等临时下载在Runner内部 `data/`，不公开提交；GitHub Action上传的审计产物保留7天。
- 若发现全国或省级来源有新版正式名单，先核查新附件和项目号，拟立项转正式立项**更新状态**，不能再加1项。

## 质量问题和已知缺口
1. 省级历史首批2355条为程序提取、仍待逐条抽检；云南210/实抓209、山东556/实抓554，缺3条。
2. 浙江2026 PDF官方跳转跨域被合法访问限制挡住，不能直接宣称已采齐；广东附件验证码不能绕过。
3. 国社科、国自然尚缺完整、可公开直接批量解析的逐项结果列表；公告页监测运行成功不等于逐项资助项目采齐。
4. GitHub Action主状态“success”仅表示流程成功，实际采集源数量与受阻情况必须读 `data/grant_hourly/grant_source_audit.json`。

## 核查
- 每小时采集工作流：https://github.com/gaolingxi/idea/actions/workflows/hourly-three-grant-sources.yml
- 官方省级项目数据：https://github.com/gaolingxi/idea/blob/main/public_metadata/provincial_socsc_projects.csv
- 31省来源：https://github.com/gaolingxi/idea/blob/main/sources/provincial_socsc_registry.json
