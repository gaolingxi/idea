# OPENCODE_TASK.md
TASK_ID: IDEA_XHS_AUTHORIZED_COLLECTION_V1_20261107
STATUS: BLOCKED_LOCAL_OFFLINE
NEXT_ACTOR: OpenCode
AUTOMATION_READY: false

## 目标
只执行小红书**合规可行性试采**。ChatGPT 已编写脚本；OpenCode 不得编写绕过平台限制的替代爬虫。滚动窗口为最近24个月。

## 步骤
1. 项目根目录运行 `python -m unittest discover -s tests -v`。
2. 查验拟采资料的许可依据、官方服务协议与 robots；将证据只存入本地 `logs/xhs_rights_review.md`。不具备许可则停止并报告。
3. 如有获准的数据导出，按 `examples/approved_export_template.csv` 准备本地 CSV，运行 `python scripts/xhs_approved_ingest.py import-export --source data/xhs/approved_export.csv`。
4. 如有逐条许可的公开页 URL，按 `examples/approved_url_template.csv` 准备清单，用 `python scripts/xhs_approved_ingest.py fetch-approved --source data/xhs/approved_urls.csv --max-pages 10` 试采无需登录的HTML元数据。遇到平台条款禁止、robots拒绝、401/403/429或验证码立即停止；不得用Cookie提取、代理轮换、伪装客户端、私有API、模拟登录解决。
5. SQLite 和日志只保存本项目的本地 `data/`、`logs/`；不要上传公开仓库。总结许可数、成功数、重复数、日期缺失数和拒绝原因。区分正文与元数据。
6. 通过修改 `OPENCODE_REPORT.md` 报告结果。没有数据时标明 BLOCKED，不能宣称已采集。

## 科学停止条件
首批至多10条；拿不到合规资料则停止并呈报。下一轮是否扩量由ChatGPT审核，不自动每小时本地抓取。
