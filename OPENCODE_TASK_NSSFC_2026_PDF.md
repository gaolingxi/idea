# OpenCode 专项任务｜国社科2026拟立项PDF附件直链与题目抽取

TASK_ID: IDEA_NSSFC_2026_SU_SE_PDF_LINKS_V1
STATUS: READY_FOR_LOCAL_OPENCODE
NEXT_ACTOR: OpenCode
PRIORITY: P0
MODE: ChatGPT编写代码 / OpenCode只执行并回写报告
SOURCE: https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm
SCOPE: 仅该高校转发的国社科2026年度拟立项公告及4类附件（重点/一般/青年/西部）
EXCLUDES: 无关社科项目、社交平台、其他科研项目

## 目标和原因
ChatGPT远程网页工具打开此公告超时，PDF附件名称能由搜索检索但**直链和文件内容尚未核实**。请在本地正常联网环境检验能否合法读取公告及可公开下载的附件。优先解析公开HTML中的 <a href> 和公开跳转；不能臆造任何链接。若页面可读，下载四个类别PDF并解析逐项项目题目，准确标注“拟立项公示”，不得写成“正式立项”。

## 执行指令
0. 必须先在本项目文件夹中运行。禁止将工作路径或输出保存到仓库之外，不改其他项目。阅读 `AGENTS.md` 和本任务即可；不要执行根目录 XHS 任务。
1. 运行环境内正常网络访问时：
   ```bash
   python -m pip install -r requirements-site-crawler.txt
   python -m py_compile scripts/inspect_nssfc_2026_pdf_links.py
   python scripts/inspect_nssfc_2026_pdf_links.py --url https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm --out-dir data/nssfc_2026_suse --max-pdfs 4
   ```
2. 查看 `data/nssfc_2026_suse/link_probe_report.json`，明确4份PDF的真实URL、HTTP访问结果、实际下载份数、PDF页数、可核实表格行数。
3. 如四份PDF可正常公开下载，抽查每类的第一页/末页及10个项目（核对类别、题目、编号、负责人、单位）；如果PDF仅为扫描件或不含标准表格，标注“需人工核对”，不使用OCR猜题目。
4. 对照全国哲学社会科学工作办公室的2026年度国家社科基金公告核对公示期、最终批复状态。2026年10月10日高校转发的附件在本任务中**只能记为拟立项**，除非另有全国社科办正式公告与逐项证据，不能按“正式立项”写入。
5. 不自动将未经人工核实的 `data/nssfc_2026_suse/nssfc_2026_proposed_candidates.csv` 与已有国社科正式立项数据合并。若发现同项目后续正式立项，应按项目编号或题目+负责人去重更新状态。
6. 回写仓库独立报告 `OPENCODE_REPORT_NSSFC_2026_PDF.md`，写清每项结果、源链接、成功下载数量、提取行数、失败原因及下一步；不得删除已有文件或覆盖原主线任务。若本地没有网络或源站阻止访问，报告BLOCKED，不允许制造成功结果。

## 安全与停止条件
- 只访问公开、允许正常访问的页面。尊重robots和站点许可；遇登录、验证码、401/403/429、Cloudflare等限制，停止对应附件，不进行绕过、不用代理或私有接口。
- 链接跳转到其他域名，必须先核查确属合法公开官方承载域名并更新白名单后才允许访问，禁止任意跳转抓取。
- 可访问的PDF原文和本地报告保存在项目内部 `data/`、`logs/`，不得提交公开仓库；GitHub只保留来源网址和许可范围内的公开书目元数据。
- 不改代码；如脚本能力不足，回报具体故障，由ChatGPT迭代脚本。只做这一支线，验收后回主线。
