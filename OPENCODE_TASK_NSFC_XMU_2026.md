# NSFC XMU Economics 2026 — isolated rowwise staging
TASK_ID: NSFC_XMU_ECON_2026_STAGING
TASK_VERSION: 1
STATUS: READY
EXECUTOR: OpenCode
NEXT_ACTOR: OpenCode
AUTOMATION_READY: false

Run only inside gaolingxi/idea:
`python scripts/stage_nsfc_xmu_economics_2026.py`

Prerequisites: requests and beautifulsoup4. Respect robots and HTTP restrictions; if denied, report BLOCKED without workarounds.
Output only to project-local data/nsfc_xmu_economics_2026_staged.csv (do not commit raw output before audit).
Compare against existing 46-row public_metadata file by approval number. Confirm 23 rows and investigate **published 9-digit approval number 126011017 (王晨笛)** against official NSFC public record; do not silently correct or discard.
Report count, anomalies, official source and evidence in OPENCODE_REPORT_NSFC_XMU_2026.md.
Do not alter CURRENT_TASK.md, frozen NSSFC 6065 rows, existing public_metadata, or other OpenCode tasks. Do not treat this file as checker-authorized until separately assigned.
