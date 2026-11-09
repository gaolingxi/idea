#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect only university-published NSFC project-level award tables (2025-2026).

Does not pretend to represent all funded NSFC awards. The official 2026 notice
lists national totals but does not itself reveal 69,563 individual project titles.
This script fetches permitted public pages, recognizes explicit table headers,
requires an 8-digit project approval number, and writes an auditable PARTIAL index.
Never bypass robots/auth/403/429/CAPTCHA, never fetch non-allowlisted domains.
"""
import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from crawl_official_sites import SiteFetcher

FIELDS = ["scheme","award_year","approval_number","project_title","principal_investigator",
          "institution","reporting_unit","project_type","application_code",
          "funding_amount","source_url","source_level","collection_scope",
          "publication_date","review_state"]
HEADERS = {
    "approval_number":("项目批准号","批准号","项目编号","批号"),
    "project_title":("项目名称","课题名称","项目题目"),
    "principal_investigator":("负责人","项目负责人","申请人","主持人"),
    "project_type":("项目类别","资助类别","类别"),
    "application_code":("申请代码","学科代码","申请代码1"),
    "funding_amount":("批准经费万元","直接经费","资助金额"),
}
def norm(s):
    return re.sub(r"\s+","",str(s or "")).strip()

def find_header(table):
    for i,tr in enumerate(table.find_all("tr")[:8]):
        cells=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["td","th"],recursive=False)]
        if not cells:continue
        mapping={}
        for key, aliases in HEADERS.items():
            matches=[j for j,c in enumerate(cells) if c in aliases or any(c.startswith(z) and len(c)<=len(z)+3 for z in aliases)]
            if matches:mapping[key]=matches[0]
        if all(x in mapping for x in ("approval_number","project_title","principal_investigator")):
            return i,mapping
    return None,None

def parse_tables(html,source):
    soup=BeautifulSoup(html,"html.parser")
    found=[]
    for table in soup.find_all("table"):
        trs=table.find_all("tr")
        start,col=find_header(table)
        if col is None:continue
        for tr in trs[start+1:]:
            vals=[norm(c.get_text(" ",strip=True)) for c in tr.find_all(["td","th"],recursive=False)]
            def val(k):
                j=col.get(k)
                return vals[j] if j is not None and j<len(vals) else ""
            approval=val("approval_number")
            title=val("project_title")
            pi=val("principal_investigator")
            if not re.fullmatch(r"\d{8}",approval):
                continue
            if not (len(title)>=5 and re.search(r"[\u4e00-\u9fff]",title) and len(pi)>=2):
                raise ValueError(f"Malformed public award row: {source['id']}, no={approval}")
            found.append({
                "scheme":"nsfc","award_year":str(source["year"]),
                "approval_number":approval,"project_title":title,
                "principal_investigator":pi,
                "institution":source["institution"],
                "reporting_unit":source["unit"],
                "project_type":val("project_type"),
                "application_code":val("application_code"),
                "funding_amount":val("funding_amount"),
                "source_url":source["url"],
                "source_level":"university_published_award_list",
                "collection_scope":"partial_institution_records_not_nationwide",
                "publication_date":"",
                "review_state":"pending_crosscheck_with_NSFC_public_record",
            })
    return found

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--registry",default="sources/nsfc_award_source_registry.json")
    parser.add_argument("--output",default="public_metadata/nsfc_awards_2025_2026_partial.csv")
    parser.add_argument("--audit",default="reports/nsfc_awards_2025_2026_seed_audit.json")
    args=parser.parse_args()
    root=Path.cwd().resolve()
    def inside(relative):
        p=(root/relative).resolve()
        if root not in p.parents and p!=root:
            raise ValueError("No files outside active idea repository")
        return p
    registry=json.loads(inside(args.registry).read_text(encoding="utf-8"))
    sources=registry["sources"]
    fetcher=SiteFetcher(min_delay=2,timeout=16)
    existing={}
    out=inside(args.output)
    if out.is_file():
        with out.open(newline="",encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("scheme")=="nsfc" and row.get("approval_number","").isdigit():
                    existing[row["approval_number"]]=row
    discovered={}
    log=[]
    for source in sources:
        result={"source_id":source["id"],"source_url":source["url"],"year":source["year"],
                "result":"not_attempted","rows":0}
        try:
            domain=urlparse(source["url"]).hostname
            if domain not in source["allowed_hosts"]:
                raise PermissionError("source hostname not in fixed source allowlist")
            final,raw,ctype,encoding=fetcher.get(source["url"],source["allowed_hosts"])
            if "html" not in ctype.lower():
                raise ValueError("Non-HTML official university notice")
            soup=BeautifulSoup(raw,"html.parser",from_encoding=encoding)
            rows=parse_tables(str(soup),source)
            if len(rows)<source.get("min_rows",1):
                raise ValueError("No structured NSFC awards with approval numbers found")
            for row in rows:
                key=row["approval_number"]
                old=discovered.get(key) or existing.get(key)
                if old and (old.get("project_title")!=row["project_title"]
                            or old.get("principal_investigator")!=row["principal_investigator"]):
                    raise ValueError(f"Conflicting approval number {key} in source {source['id']}")
                discovered[key]=row
            result.update(result="collected",rows=len(rows),final_url=final)
        except Exception as exc:
            result.update(result="failed_or_blocked",reason=f"{type(exc).__name__}:{str(exc)[:140]}")
        log.append(result)
    # Never report success for an all-empty or blocked run.
    if not discovered:
        status="BLOCKED_NO_NEW_PROJECT_LEVEL_SOURCES"
    else:
        status="PARTIAL_PROJECT_LEVEL_SEED_COLLECTED"
    for key,row in discovered.items():
        existing[key]=row
    audit={
        "checked_at":datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "status":status,"national_scope":"partial_university_award_lists",
        "new_or_verified_approval_numbers":len(discovered),
        "index_total_unique_approval_numbers":len(existing),
        "official_2026_total_notice":"https://www.nsfc.gov.cn/p1/3381/2822/141011.html",
        "official_total_is_not_titles":True,
        "sources":log
    }
    audit_path=inside(args.audit)
    audit_path.parent.mkdir(parents=True,exist_ok=True)
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
    if discovered:
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS)
            w.writeheader()
            w.writerows(sorted(existing.values(),key=lambda x:(x["award_year"],x["approval_number"])))
    print(json.dumps(audit,ensure_ascii=False,indent=2))
    return 0 if discovered else 2

if __name__=="__main__":
    raise SystemExit(main())
