TASK_ID: IDEA_NSFC_PROJECT_LEVEL_SEED_V1_20261109
TASK_VERSION: 1
STATUS: PENDING
EXECUTOR: OPENCODE
NEXT_ACTOR: OPENCODE
AUTOMATION_READY: YES
AUTOMATION_REQUIRED_FILES: OPENCODE_TASK_NSFC_SEED.md;scripts/collect_nsfc_awards_from_universities.py;sources/nsfc_award_source_registry.json;requirements-site-crawler.txt;AGENTS.md

# idea checker 自动领取｜国自然首批项目级名单

收到本项目 Orca OpenCode 的“继续”后：

1. 在 idea/repo 检查 git status，工作树干净时使用 git pull --ff-only origin main 同步。
2. 仔细阅读 OPENCODE_TASK_NSFC_SEED.md，执行 scripts/collect_nsfc_awards_from_universities.py；只采官方公开大学网站项目批准号、名称、负责人，不把局部大学项目列表当全国汇总。
3. 核实基金委公开知识平台 kd.nsfc.cn 可查询情况；访问受限即报告，不绕过限制。
4. 回写 OPENCODE_REPORT_NSFC_SEED.md 及 OPENCODE_REPORT_AUTORUN.md 的 TASK_ID、TASK_VERSION、STATUS 与真实结果。允许的公开元数据与审计JSON经检查后提交GitHub；不提交 data/、logs/、原PDF。
5. 国社科已结案，严禁继续原来的NSSFC任务。执行一批即止，不自动创建其他科研任务。
