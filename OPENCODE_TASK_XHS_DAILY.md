TASK_ID: IDEA_XHS_DAILY_CLUES_V1_20261125
TASK_VERSION: 2
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_XHS_DAILY.md;scripts/prepare_xhs_daily_clues.py;AGENTS.md

# 每日小红书合规线索交接｜首次本地执行

国自然 v2 已回传 PARTIAL_DONE，保留独立任务和报告。用户要求本地执行。首次只做合规来源及输入核查、运行已有整理代码、产出实际回执。没有授权输入即 BLOCKED，不自动抓取。可通过普通公开搜索引擎索引寻找公开学术线索，并回溯论文/政府官方源；只有独立核实的公开政策/论文来源才可作为另行标记的学术线索，不能声称看过小红书原帖，不得借搜索索引绕过平台访问控制或把索引当作授权。未经许可不上传小红书正文、账号内容或受限资料。无合格输入不得生成虚假记录。

## 输入及边界
关注 Kenny思享、大山经管资料、iiiiop、土豆学姐（研究ing），仅处理合法获取且明确允许公开分享的研究线索。已有权限审查为 BLOCKED；没有授权资料时停止，不抓取网站、不绕过限制。不得自动登录、提取 Cookie、使用私有接口或模拟浏览器规避平台限制。用户或获准来源准备本地 data/xhs/daily_approved_clues.csv，表头：
account,published_at,source_url,concept,allow_collect,allow_public_share,authorization_reference
concept 是独立归纳的简短研究概念，不得粘贴正文、标题全文、截图、评论、个人资料或付费内容。授权凭据仅留本地，不提交。只有明确批准采集并公开分享的行才进入处理。账号需人工核实；发布日期必须实际核实。

## 执行
1. 检查 AGENTS.md 及当前任务，确认当前任务为本任务 v2，不覆盖其他任务。
2. 获得授权输入后运行 python scripts/prepare_xhs_daily_clues.py。
3. 审查输出 sources/xhs_daily/latest.json（仅账号公开名称、发布日期、去掉参数的原帖链接、独立归纳概念、审核状态）。必须确认无个人隐私、笔记正文、凭证、受限或未获公开分享许可的内容。未通过则停止，不上传。
4. 只在审查通过且仓库状态无冲突时提交该 JSON；可保留日期快照，但不能覆盖远端更新。每天北京时间次日上午9点前准备最新记录，需现有任务空闲、获准输入以及本地执行条件均满足；未确认本地周期调度前不宣称已自动运行。
5. 回写独立 OPENCODE_REPORT_XHS_DAILY.md，记录真实输入条数、有效条数、拒绝数、覆盖账号及日期、提交 SHA、未访问的账号和原因。不提交原始 CSV 或 data/、logs/。无输入则 BLOCKED，不覆盖旧快照。
ChatGPT 每日读取 latest.json 检查 generated_at、published_at 与状态，不将线索视为已核实政策；再回溯政策或论文原始出处。

