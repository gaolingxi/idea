# OpenCode 专项任务｜国社科2026年度项目公示完整名册核验

TASK_ID: IDEA_NSSFC_2026_FULL_6065_PROPOSED_V1
TASK_VERSION: 3
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES

## 科研目标
已有四份PDF下载成功、已提取5931条公开题目。现在要补齐完整的**6065项公示记录**：另有134项公开材料显示“题目略”，不是134条抓取失败或可推断的题目。不得捏造题目、编号或把拟立项改正式立项。

## 执行
1. 在 idea Git 仓库根目录（嵌套于 idea/repo），仅做本项目工作，确保工作树没有未经处理的本地变动。
2. 使用 ChatGPT 已写好的脚本，禁止另造替代爬虫：
```bash
python -m py_compile scripts/audit_nssfc_2026_full_proposed.py
python scripts/audit_nssfc_2026_full_proposed.py --input-dir data/nssfc_2026_suse --output public_metadata/national_socsc_2026_annual_proposed.csv --audit reports/nssfc_2026_annual_proposed_audit.json
```
3. 脚本只使用本地已下载的4份PDF；逐表保留全部编号（这是名单内**序号**，不是批准号）、学科、负责人、依托单位、项目类别、PDF页码和来源；134项题目未公开者`title`留空，`original_title_cell`保留原字“略”，`title_is_public=no`。
4. **强制质量闸门**：四类分别444/2705/2350/566；合计6065；公开题目5931；未公开题目134；5931行内容与前次提取CSV逐条（题目+负责人+单位+类别）完全一致；序号无断号/重复；均合格才允许入库。实际PDF结构不满足任一项则报告BLOCKED/FAILED，并保留差异实例，不强行提交CSV。
5. 成功后检查公开CSV只有允许公开的项目元数据，不含原PDF、私人资料、Cookie或密钥；提交 `public_metadata/national_socsc_2026_annual_proposed.csv`、`reports/nssfc_2026_annual_proposed_audit.json` 和本专项报告至 `gaolingxi/idea`，不提交 `data/`、`logs/` 下的PDF和原始文件。
6. 回写 `OPENCODE_REPORT_NSSFC_2026_FULL_ROSTER.md` 和 `OPENCODE_REPORT_AUTORUN.md`，状态写真实DONE/FAILED/BLOCKED，NEXT_ACTOR: ChatGPT。报告应说明4类公示行数、题目略数、校验情况、审计文件链接。
7. 不执行其他项目，也不修改旧版 v3 成功报告。之后由ChatGPT继续核对正式批复与重大/专项名单、国自然、省社科。

## 科学停止条件
此支线在6065项全量公示名册完整、5931公开题目全部对齐、134项不公开题目得到保留、元数据成功入库后停止；不自动创建新任务、不做关键词选题评分。

## v2 本轮修复说明
四份原PDF表头为「申请人」，v1 脚本的 person 列词表遗漏该名称导致0行、已如实报告FAILED。v2 只修复该表头，测试已改用真实表头；重新运行原四份PDF的完整6065行审核，严禁跳过质量闸门或把拟立项当正式立项。原 v1 FAILED 报告保留作证据。

## v3 质量闸门修复
v2 实测四类444/2705/2350/566，公开题目5931、略134；此前5931条在不含类别时内容零差异。v3 将英文类别key/general/young/western严格映射到重点/一般/青年/西部，再逐条比较全部四字段；**不删除类别核验、不放松闸门**。保留旧FAILED报告并重新执行。
