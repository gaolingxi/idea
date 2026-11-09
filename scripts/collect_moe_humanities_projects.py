#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract 2025 formal / 2026 PUBLICITY MOE humanities funded-project names.

Strictly source-scoped, no access bypass. Award totals are not row-level data.
Each attachment is published only after exact sequence/count/field audits pass.
The 2026 publicity has NO final award status, and no invented approval numbers.
"""
import argparse
import csv
import io
import json
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

import pdfplumber
import requests

FIELDS=[
 "scheme","year","listing_group","list_sequence","discipline","project_title",
 "project_category","project_approval_number","principal_investigator","university",
 "award_status","publisher","official_notice_url","pdf_url","pdf_page",
 "pdf_source_level","review_state"
]
KEYWORDS={
 "list_sequence":("序号","编号","序"),
 "discipline":("学科门类","所属学科","学科","学科类别"),
 "project_title":("项目名称","课题名称","项目题目","课题题目"),
 "project_category":("项目类别","项目类型","类别","资助类别"),
 "project_approval_number":("项目批准号","批准号","项目编号","批准编号"),
 "principal_investigator":("申请人","负责人","项目负责人","主持人","首席专家"),
 "university":("学校名称","申请学校","依托单位","单位名称","所在学校","学校","投标单位")
}
USER_AGENT="Mozilla/5.0 (compatible; AcademicPublicResearchData/1.0; human-reviewed)"
def compact(v):
    return re.sub(r"\s+","",str(v or "").replace("\u200b","")).strip()

def match_cell(cell,names):
    text=compact(cell)
    return any(text==name or (text.startswith(name) and len(text)<=len(name)+3) for name in names)

def columns_from_head(matrix):
    for i,row in enumerate(matrix[:5]):
        if not row:continue
        mapping={}
        for key,names in KEYWORDS.items():
            positions=[k for k,val in enumerate(row) if match_cell(val,names)]
            if positions:mapping[key]=positions[0]
        required=("list_sequence","project_title","principal_investigator","university")
        if all(k in mapping for k in required):
            return i,mapping
    return None,None

def extract_pdf(pdf_path,source):
    records=[];headers=[];seen=set()
    with pdfplumber.open(pdf_path) as document:
        pages=len(document.pages)
        prev_cols=None
        for page_no,page in enumerate(document.pages,1):
            tables=page.extract_tables({"vertical_strategy":"lines","horizontal_strategy":"lines"})
            if not tables:
                tables=page.extract_tables()
            # Nothing is silently invented from extraction failures.
            for matrix in tables or []:
                if not matrix:continue
                idx,col=columns_from_head(matrix)
                if idx is not None:
                    start=idx+1
                    prev_cols=(len(matrix[idx]),col)
                    if len(headers)<4:headers.append([compact(x) for x in matrix[idx]])
                elif prev_cols and len(matrix[0])==prev_cols[0]:
                    start=0
                    col=prev_cols[1]
                else:
                    continue
                for cellrow in matrix[start:]:
                    if not cellrow:continue
                    def pick(name):
                        j=col.get(name)
                        return compact(cellrow[j]) if j is not None and j<len(cellrow) else ""
                    serial=pick("list_sequence")
                    if not re.fullmatch(r"[0-9]{1,6}",serial):
                        continue
                    seq=int(serial)
                    if seq in seen:
                        raise ValueError(f"{source['id']}: duplicate sequence {seq}")
                    seen.add(seq)
                    title=pick("project_title")
                    person=pick("principal_investigator")
                    university=pick("university")
                    approval=pick("project_approval_number")
                    category=pick("project_category")
                    discipline=pick("discipline")
                    if not title or not person or not university:
                        raise ValueError(f"{source['id']}: missing project title / applicant / university on #{seq}, PDF p{page_no}")
                    if source["year"]==2025 and not re.fullmatch(r"25[A-Za-z0-9]{4,20}",approval):
                        raise ValueError(f"{source['id']}: invalid 2025 approval number {approval!r} for #{seq}")
                    if source["year"]==2026:
                        # Publicity stage; no fabricated approval numbers.
                        approval="" if not approval else approval
                    records.append({
                        "scheme":"moe_humanities_social_science",
                        "year":str(source["year"]),
                        "listing_group":source["group"],
                        "list_sequence":serial,
                        "discipline":discipline,
                        "project_title":title,
                        "project_category":category,
                        "project_approval_number":approval,
                        "principal_investigator":person,
                        "university":university,
                        "award_status":source["status"],
                        "publisher":source["publisher"],
                        "official_notice_url":source["notice_url"],
                        "pdf_url":source["pdf_url"],
                        "pdf_page":str(page_no),
                        "pdf_source_level":source["source_level"],
                        "review_state":"original_pdf_table_extracted_pending_spotcheck",
                    })
    return records,{"pages":pages,"sample_headers":headers,"first_records":records[:2]}

def get_url_with_policy(session, url, allowed_hosts,cache):
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in allowed_hosts:
        raise PermissionError("URL not HTTPS or not in source-specific host allowlist")
    origin=f"{parsed.scheme}://{parsed.netloc}"
    if origin not in cache:
        robots=session.get(origin+"/robots.txt",timeout=18,allow_redirects=True)
        if robots.status_code==404:
            cache[origin]=RobotFileParser()
            cache[origin].parse([])
        elif robots.status_code==200:
            rp=RobotFileParser()
            rp.parse(robots.text.splitlines())
            cache[origin]=rp
        else:
            raise PermissionError(f"robots retrieval returned {robots.status_code}")
    if not cache[origin].can_fetch(USER_AGENT,url):
        raise PermissionError("robots.txt disallows this PDF")
    time.sleep(1.5)
    resp=session.get(url,timeout=65,allow_redirects=True,stream=True)
    if resp.status_code in (401,403,429):
        raise PermissionError("HTTP access restricted: "+str(resp.status_code))
    resp.raise_for_status()
    if urlparse(resp.url).scheme!="https" or urlparse(resp.url).hostname not in allowed_hosts:
        raise PermissionError("redirect left source-specific host allowlist")
    result=bytearray()
    for chunk in resp.iter_content(chunk_size=65536):
        result.extend(chunk)
        if len(result)>24000000:
            raise ValueError("PDF exceeds 24MB safety limit")
    if not result.startswith(b"%PDF"):
        raise ValueError(f"received non-PDF body; status={resp.status_code}, content_type={resp.headers.get('content-type')}")
    return bytes(result),resp.url

def run(args):
    root=Path.cwd().resolve()
    def inroot(path):
        p=(root/path).resolve()
        if root!=p and root not in p.parents:raise ValueError("Project files must stay inside repo")
        return p
    registry=json.loads(inroot(args.registry).read_text("utf-8"))
    audit_path=inroot(args.audit)
    output=inroot(args.output)
    session=requests.Session()
    session.headers.update({"User-Agent":USER_AGENT,"Accept-Language":"zh-CN,zh;q=0.8"})
    robots={}
    rows=[];audits=[];keys=set()
    for src in registry["groups"]:
        item={"id":src["id"],"year":src["year"],"group":src["group"],
              "status":src["status"],"expected_count":src["expected"],
              "notice_url":src["notice_url"],"pdf_url":src["pdf_url"],
              "result":"NOT_RUN","published_count":0}
        try:
            location=inroot("data/moe_humanities/pdf/"+src["id"]+".pdf")
            location.parent.mkdir(parents=True,exist_ok=True)
            if args.use_cache and location.exists() and location.stat().st_size>1000:
                pdfbytes=location.read_bytes();final=src["pdf_url"]
            else:
                pdfbytes,final=get_url_with_policy(session,src["pdf_url"],src["allowed_hosts"],robots)
                location.write_bytes(pdfbytes)
            group,info=extract_pdf(location,src)
            item["pages"]=info["pages"];item["sample_headers"]=info["sample_headers"]
            item["extracted_count"]=len(group)
            item["sample_project_titles"]=[x["project_title"][:100] for x in group[:2]]
            if len(group)!=src["expected"]:
                raise ValueError(f"extracted {len(group)} rows, source-specific official expected {src['expected']}")
            if {int(r["list_sequence"]) for r in group}!=set(range(1,src["expected"]+1)):
                raise ValueError("sequence 1..N not complete")
            for r in group:
                key=(r["year"],r["listing_group"],r["list_sequence"])
                if key in keys:raise ValueError(f"duplicated record key {key}")
                keys.add(key)
            rows.extend(group)
            item.update(result="PASS",published_count=len(group),actual_pdf_url=final)
        except Exception as e:
            item.update(result="BLOCKED_OR_FAILED",reason=f"{type(e).__name__}:{str(e)[:250]}")
        audits.append(item)
        print("GROUP",json.dumps(item,ensure_ascii=False,sort_keys=True),flush=True)
    groups_passed=[v for v in audits if v["result"]=="PASS"]
    # Across groups, approved projects must not reuse an official approval number.
    all_approval_numbers=[r["project_approval_number"] for r in rows if r["project_approval_number"]]
    if len(all_approval_numbers)!=len(set(all_approval_numbers)):
        raise ValueError("Duplicate official MOE approval number across attached lists; refuse to publish")
    total_by_year=Counter(row["year"] for row in rows)
    report={
      "run_time":datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
      "source_count":len(audits),
      "passed_groups":len(groups_passed),
      "per_source":audits,
      "persisted_project_rows":len(rows),
      "by_year":dict(total_by_year),
      "2025_formal_vs_2026_publicity":"2025=ministerial formal awards; 2026=publicity only",
      "note":"Only exact-count PDF table rows are exported. Other groups remain BLOCKED, not inferred.",
    }
    audit_path.parent.mkdir(parents=True,exist_ok=True)
    audit_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    if rows:
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("w",encoding="utf-8-sig",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(sorted(rows,key=lambda x:(x["year"],x["listing_group"],int(x["list_sequence"]))))
    print("SUMMARY",json.dumps({k:v for k,v in report.items() if k!="per_source"},ensure_ascii=False))
    return 0 if rows else 2

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--registry",default="sources/moe_humanities_2025_2026_registry.json")
    p.add_argument("--output",default="public_metadata/moe_humanities_2025_2026_projects.csv")
    p.add_argument("--audit",default="reports/moe_humanities_2025_2026_audit.json")
    p.add_argument("--use-cache",action="store_true")
    return run(p.parse_args())

if __name__=="__main__":
    raise SystemExit(main())
