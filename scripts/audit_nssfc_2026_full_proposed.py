#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conservatively rebuild 2026 NSSFC ANNUAL *proposed* full roster from 4 public PDFs.

Critical distinctions:
- 6065 announcement rows are NOT 6065 published titles.
- 134 title-omitted rows are kept as records with blank title; never invented.
- Any mismatch against the official announcement or existing 5931 extracted
  public titles fails closed: NO output is published.
- No request, PDF, user/private data, or credential is uploaded to GitHub.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pdfplumber

NOTICE_URL="https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm"
PDFS = {
    "key": ("https://download.people.com.cn/yunying2/twentyfive17914600301.pdf",444),
    "general": ("https://download.people.com.cn/yunying2/twentyfive17914600601.pdf",2705),
    "young": ("https://download.people.com.cn/yunying2/twentyfive17914600921.pdf",2350),
    "western": ("https://download.people.com.cn/yunying2/twentyfive17914601111.pdf",566),
}
FIELDS = (
    "fund","year","award_status","category","list_sequence","discipline","title",
    "title_is_public","original_title_cell","person","unit","project_id",
    "source_notice","attachment_url","pdf_page","provenance","review_state"
)

def norm(v):
    return re.sub(r"\s+", "", str(v or "")).strip()

def match_col(text, words):
    s=norm(text)
    return any(s == w or (w in s and len(s) <= len(w)+3) for w in words)

def header_map(rows):
    keys={
        "list_sequence": ("序号",),
        "discipline": ("涉及学科","学科"),
        "title": ("课题名称","项目名称","课题题目"),
        "person": ("负责人","申请人","主持人"),
        "unit": ("依托单位","责任单位","工作单位"),
    }
    for i,row in enumerate(rows[:6]):
        if not row:continue
        cols={}
        for k,words in keys.items():
            cols[k]=next((j for j,c in enumerate(row) if match_col(c,words)),None)
        if all(cols[k] is not None for k in ("list_sequence","title","person","unit")):
            return i,cols
    return None,None

def extract(path,category,attachment_url):
    rows, seen, examples = [], set(), []
    carry=None
    with pdfplumber.open(path) as pdf:
        for page_number,page in enumerate(pdf.pages,1):
            for table in page.extract_tables() or []:
                if not table:continue
                h,cols=header_map(table)
                if cols is not None:
                    carry=(len(table[h]),cols)
                    start=h+1
                elif carry and len(table[0])==carry[0]:
                    cols=carry[1]
                    start=0
                else:continue
                for line in table[start:]:
                    if not line:continue
                    def at(key):
                        j=cols.get(key)
                        return norm(line[j]) if j is not None and j<len(line) else ""
                    sequence=at("list_sequence")
                    if not re.fullmatch(r"\d{1,6}",sequence):
                        continue
                    if sequence in seen:
                        # A repeated row is not silently counted twice.
                        raise ValueError(f"{category}: duplicate visible sequence {sequence}")
                    seen.add(sequence)
                    raw_title=at("title")
                    # Titles are not public when the official table explicitly omits them.
                    is_omitted=(raw_title in ("","略","课题名称略","项目名称略")
                                or raw_title.endswith("题目略") or raw_title.endswith("名称略"))
                    if not is_omitted and (not re.search(r"[\u4e00-\u9fff]",raw_title) or len(raw_title)<5):
                        raise ValueError(f"{category} seq={sequence}: unexpected title cell {raw_title!r}")
                    person=at("person");unit=at("unit")
                    if not person or not unit:
                        raise ValueError(f"{category} seq={sequence}: missing PI or unit")
                    row={
                        "fund":"national_social_science_fund",
                        "year":"2026",
                        "award_status":"proposed_publicity_not_formal_award",
                        "category":category,
                        "list_sequence":sequence,
                        "discipline":at("discipline"),
                        "title":"" if is_omitted else raw_title,
                        "title_is_public":"no" if is_omitted else "yes",
                        "original_title_cell":raw_title,
                        "person":person,
                        "unit":unit,
                        "project_id":"", # no approval numbers in this publicity list
                        "source_notice":NOTICE_URL,
                        "attachment_url":attachment_url,
                        "pdf_page":str(page_number),
                        "provenance":"publicly_accessible_People_cn_PDF_linked_by_SUSE_notice",
                        "review_state":"public_original_table_pending_final_award_confirmation",
                    }
                    rows.append(row)
                    if len(examples)<3:examples.append((sequence,raw_title[:35],person,unit))
        return rows, {"pages":len(pdf.pages),"examples":examples}

def existing_candidates(path):
    if not path.is_file():raise FileNotFoundError("Expected 5931-row OpenCode candidate CSV: "+str(path))
    with path.open(newline="",encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=5931:
        raise ValueError(f"Prior extracted candidate count mismatch: {len(rows)} != 5931")
    keys=[(norm(r["project_category"]),norm(r["project_title"]),
           norm(r["principal_investigator"]),norm(r["organization"])) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError("Duplicate rows in previously extracted 5931 candidate CSV")
    return set(keys)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",default="data/nssfc_2026_suse")
    ap.add_argument("--output",default="public_metadata/national_socsc_2026_annual_proposed.csv")
    ap.add_argument("--audit",default="reports/nssfc_2026_annual_proposed_audit.json")
    args=ap.parse_args()
    root=Path.cwd().resolve()
    directory=Path(args.input_dir).resolve()
    output=Path(args.output).resolve()
    audit=Path(args.audit).resolve()
    for path in (directory,output,audit):
        if path!=root and root not in path.parents:
            raise SystemExit("All inputs and outputs must be inside the current Git repository")
    records=[]
    source_audit={}
    for category,(url,expected) in PDFS.items():
        file=directory / (hashlib.sha256(url.encode()).hexdigest()[:16]+".pdf")
        if not file.is_file():raise FileNotFoundError("Missing original local PDF "+str(file))
        rows,info=extract(file,category,url)
        published=sum(x["title_is_public"]=="yes" for x in rows)
        unpublished=len(rows)-published
        source_audit[category]={"expected":expected,"extracted":len(rows),
            "published_titles":published,"titles_not_public":unpublished,
            "pages":info["pages"],"examples":info["examples"],
            "source_pdf":url}
        if len(rows)!=expected:
            raise ValueError(f"{category}: PDF table has {len(rows)} rows but original announcement has {expected}; NOT PUBLISHING")
        # Numeric sequence numbers are used only to audit the PDF, never as official approval numbers.
        numeric={int(x["list_sequence"]) for x in rows}
        if numeric!=set(range(1,expected+1)):
            raise ValueError(f"{category}: visible serial number range incomplete; NOT PUBLISHING")
        records+=rows
    total_public=sum(r["title_is_public"]=="yes" for r in records)
    total_hidden=len(records)-total_public
    if (len(records),total_public,total_hidden)!=(6065,5931,134):
        raise ValueError(f"Global count discrepancy: all={len(records)}, published={total_public}, omitted={total_hidden}; NOT PUBLISHING")
    previous=existing_candidates(directory/"nssfc_2026_proposed_candidates.csv")
    new={(r["category"],r["title"],r["person"],r["unit"]) for r in records if r["title_is_public"]=="yes"}
    if new!=previous:
        missing=list(previous-new)[:3]
        extra=list(new-previous)[:3]
        raise ValueError(f"Mismatch against previous 5931 project candidates; missing={missing}, extra={extra}; NOT PUBLISHING")
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        w.writerows(records)
    report={
        "result":"PASSED_FULL_6065_PUBLICITY_RECORDS",
        "verified_at":datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "source_notice":NOTICE_URL,
        "status":"proposed_not_final_award",
        "total_publicity_rows":len(records),
        "public_titles":total_public,
        "title_omitted_rows":total_hidden,
        "prior_5931_candidates_exact_match":True,
        "categories":source_audit,
        "output_csv":str(output.relative_to(root)),
        "note":"Serial numbers are not award IDs. All 6065 rows are publicity-stage, not confirmed funded awards."
    }
    audit.parent.mkdir(parents=True,exist_ok=True)
    audit.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="categories"},ensure_ascii=False))
    print("BY_CATEGORY",json.dumps({k:{"total":v["extracted"],"title_omitted":v["titles_not_public"]} for k,v in source_audit.items()},ensure_ascii=False))
if __name__=="__main__":
    main()
