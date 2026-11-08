#!/usr/bin/env python3
"""Capture only publicly available provincial grant project titles from verified official PDFs.

Sources: sources/provincial_socsc_registry.json
Output: public_metadata/provincial_socsc_projects.csv; raw PDFs stay inside data/.
No OCR, authentication bypass, proxies, or speculative project names.
"""
import argparse
import csv
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pdfplumber

spec=importlib.util.spec_from_file_location("site_crawler",Path(__file__).with_name("crawl_official_sites.py"))
site=importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

HEAD_NAMES=("项目名称","课题名称","研究课题名称","项目题目","课题题目","研究题目")
HEAD_PERSON=("负责人","项目负责人","课题负责人","主持人","首席专家")
HEAD_UNIT=("责任单位","主管单位","承担单位","所在单位","工作单位")
HEAD_ID=("项目编号","项目批准号","批准号","项目编码","课题编号")
HEAD_CATEGORY=("项目类别","课题类别","项目类型","类别")
FIELDS=("province","year","status","project_id","title","person","unit","project_category",
        "source_url","attachment_url","page_number","provenance","review_state")

def clean(x):
    return re.sub(r"\s+","",str(x or "")).strip().strip("：:。，·")

def col_match(v, words):
    c=clean(v)
    for word in words:
        if word in c and len(c)<19:
            return True
    return False

def looks_title(s):
    if not (7 <= len(s) <= 190): return False
    if s in HEAD_NAMES or "立项名单" in s or s.startswith("附件"): return False
    if re.fullmatch(r"[\d一二三四五六七八九十.．、\-]+",s):return False
    return bool(re.search(r"[\u4e00-\u9fff]",s))

def index_header(rows):
    for ri,row in enumerate(rows[:6]):
        fields=[clean(c) for c in row]
        title_col=next((i for i,c in enumerate(fields) if col_match(c,HEAD_NAMES)),None)
        if title_col is None:continue
        return ri,{
            "title":title_col,
            "person":next((i for i,c in enumerate(fields) if col_match(c,HEAD_PERSON)),None),
            "unit":next((i for i,c in enumerate(fields) if col_match(c,HEAD_UNIT)),None),
            "project_id":next((i for i,c in enumerate(fields) if col_match(c,HEAD_ID)),None),
            "project_category":next((i for i,c in enumerate(fields) if col_match(c,HEAD_CATEGORY)),None)}
    return None,None

def pdf_rows(pdf_file):
    results=[]
    carry=None
    with pdfplumber.open(pdf_file) as pdf:
        for n,page in enumerate(pdf.pages,1):
            found_on_page=False
            for table in (page.extract_tables() or []):
                if not table or len(table)<2:continue
                hi,columns=index_header(table)
                if columns is not None:
                    carry=(len(table[hi]),columns)
                    start=hi+1
                elif carry and abs(len(table[0])-carry[0])==0:
                    columns=carry[1]
                    start=0
                else:continue
                for row in table[start:]:
                    if not row:continue
                    def cell(key):
                        ix=columns.get(key)
                        return clean(row[ix]) if ix is not None and ix<len(row) else ""
                    title=cell("title")
                    if not looks_title(title):continue
                    results.append((n,{key:cell(key) for key in ("title","person","unit","project_id","project_category")}))
                    found_on_page=True
            if not found_on_page:
                # Missing table rows are never guessed from OCR/text fragments.
                pass
    return results

def existing_rows(path):
    if not path.exists():return {}
    with path.open(encoding="utf-8-sig",newline="") as f:
        return {(r["province"],r["year"],r["project_id"] or clean(r["title"])+clean(r["person"])):r
                for r in csv.DictReader(f)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--province",action="append",help="Only collect listed provinces, repeatable")
    ap.add_argument("--registry",default="sources/provincial_socsc_registry.json")
    ap.add_argument("--output",default="public_metadata/provincial_socsc_projects.csv")
    ap.add_argument("--audit",default="data/provincial_socsc/crawl_audit.json")
    ap.add_argument("--delay",type=float,default=1.5)
    args=ap.parse_args()
    raw=json.loads(Path(args.registry).read_text(encoding="utf-8"))
    fetcher=site.SiteFetcher(min_delay=args.delay,timeout=20)
    db=Path(args.audit).parent
    db.mkdir(parents=True,exist_ok=True)
    out=Path(args.output)
    old=existing_rows(out)
    report=[]
    today=datetime.now(ZoneInfo("Asia/Tokyo")).date()
    try:since=today.replace(year=today.year-2).isoformat()
    except ValueError:since=today.replace(year=today.year-2,day=28).isoformat()
    targets=[r for r in raw["provinces"] if (not args.province or r["province"] in args.province)]
    for src in targets:
        r={"province":src["province"],"year":src["project_year"],
           "status":src["record_status"],"source_url":src["source_url"],
           "pdfs_fetched":0,"rows_parsed":0,"errors":[]}
        if src["record_status"] not in ("formal","proposed","formal_special","formal_reprint"):
            r["errors"].append("Not a verified whole-province project-list source")
            report.append(r);continue
        if src.get("publication_date","") and src["publication_date"]<since:
            r["errors"].append("Outside rolling two-calendar-year period")
            report.append(r);continue
        hosts=src.get("allowed_hosts") or []
        attachments=list(src.get("direct_attachment_urls") or [])
        # If no direct PDF available, follow the exact official notice to discover PDFs.
        if not attachments and src.get("source_url"):
            try:
                final,body,ctype,enc=fetcher.get(src["source_url"],hosts)
                if "html" in ctype:
                    soup,_,_=site.html_data(body,enc)
                    for url,label in site.links(soup,final,hosts):
                        path=url.lower()
                        if (path.endswith(".pdf") or "fileurl=" in path and ".pdf" in path
                            or ("附件" in label and ".pdf" in label)):
                            attachments.append(url)
            except Exception as e:
                r["errors"].append("source notice "+type(e).__name__+": "+str(e)[:140])
        attachments=list(dict.fromkeys(attachments))[:12]
        if not attachments:
            r["errors"].append("Official PDF attachments not found; XLSX/HTML/image lists pending separate parser")
        for url in attachments:
            try:
                final,body,ctype,enc=fetcher.get(url,hosts)
                if not body.lstrip().startswith(b"%PDF"):
                    r["errors"].append("Not a PDF: "+url[:110]);continue
                local=site.archive(db,src["province"],final,body,".pdf")
                r["pdfs_fetched"]+=1
                for page,values in pdf_rows(local):
                    title=values["title"]
                    row={"province":src["province"],"year":src["project_year"],
                         "status":"proposed" if src["record_status"]=="proposed" else "formal",
                         "source_url":src["source_url"],"attachment_url":final,
                         "page_number":str(page),"provenance":src["source_level"],
                         "review_state":"official_attachment_table_extracted_pending_spotcheck",**values}
                    key=(row["province"],row["year"],row["project_id"] or clean(title)+clean(values["person"]))
                    if key not in old:
                        old[key]=row
                        r["rows_parsed"]+=1
            except Exception as e:
                r["errors"].append(type(e).__name__+": "+str(e)[:180])
        report.append(r)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(old.values(),key=lambda r:(r["province"],r["year"],r["project_id"],r["title"])))
    Path(args.audit).write_text(json.dumps({"window_start":since,"window_end":today.isoformat(),"source_count":len(targets),
        "total_saved_candidate_rows":len(old),"by_province":report},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"total_saved_candidate_rows":len(old),"by_province":report},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
