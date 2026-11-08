#!/usr/bin/env python3
"""Extract eligible individual grant titles from public provincial OFFICIAL HTML tables."""
import csv, json, re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from crawl_official_sites import SiteFetcher

FIELDS=("province","year","status","project_id","title","person","unit",
        "project_category","source_url","attachment_url","page_number",
        "provenance","review_state")
TARGETS=[
 {"province":"浙江","year":"2025","status":"formal","project_category":"新型智库课题",
  "source_url":"https://www.zjskw.gov.cn/col/col1229516287/art/2025/art_2b0659dc750d40699642b9c2046ba916.html",
  "allowed_hosts":["zjskw.gov.cn"],"provenance":"province_office"},
 {"province":"内蒙古","year":"2026","status":"formal_special","project_category":"冷门绝学重点专项",
  "source_url":"https://nmgskghw.nmgnews.com.cn/system/2026/10/30/030418490_01.shtml",
  "allowed_hosts":["nmgskghw.nmgnews.com.cn"],"provenance":"province_planning_portal"}
]

def c(v):
    return re.sub(r"\s+","",str(v or "")).strip()

def col(headers,names):
    return next((i for i,h in enumerate(headers) if any(n in h for n in names)),None)

def extract(soup,src):
    result=[]
    for table in soup.select("table"):
        trs=table.find_all("tr")
        hd=None
        for ri,rr in enumerate(trs[:6]):
            headers=[c(x.get_text(" ",strip=True)) for x in rr.find_all(["th","td"],recursive=False)]
            ti=col(headers,["课题名称","项目名称"])
            pi=col(headers,["课题编号","批准号","项目编号"])
            if ti is not None and pi is not None:
                hd=(ri,{"project_id":pi,"title":ti,
                    "person":col(headers,["课题负责人","负责人","主持人"]),
                    "unit":col(headers,["智库/联盟名称","所在单位","承担单位","责任单位"]),
                    "project_category":col(headers,["课题级别","项目类型","项目类别"])})
                break
        if not hd:continue
        hi,inds=hd
        for row in trs[hi+1:]:
            cells=[c(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"],recursive=False)]
            def val(k):
                i=inds[k]
                return cells[i] if i is not None and i<len(cells) else ""
            ident=val("project_id");title=val("title")
            if not re.match(r"^\d{2,4}[A-Za-z\u4e00-\u9fff0-9]+",ident):continue
            if not (4 <= len(title) <= 220):continue
            result.append({"province":src["province"],"year":src["year"],
                "status":src["status"],"project_id":ident,"title":title,"person":val("person"),
                "unit":val("unit"),"project_category":val("project_category") or src["project_category"],
                "source_url":src["source_url"],"attachment_url":"","page_number":"",
                "provenance":src["provenance"],"review_state":"official_html_table_extracted_pending_spotcheck"})
    return result

def main():
    p=Path("public_metadata/provincial_socsc_projects.csv")
    old={}
    if p.exists():
        with p.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                old[(row["province"],row["year"],row["project_id"] or row["title"]+row["person"])]=row
    fetch=SiteFetcher(min_delay=2,timeout=18)
    report=[]
    for src in TARGETS:
        try:
            url,raw,ctype,enc=fetch.get(src["source_url"],src["allowed_hosts"])
            if "html" not in ctype:raise ValueError("not HTML")
            soup=BeautifulSoup(raw,"html.parser",from_encoding=enc)
            extracted=extract(soup,src)
            added=0
            for row in extracted:
                key=(row["province"],row["year"],row["project_id"] or row["title"]+row["person"])
                if key not in old:
                    old[key]=row;added+=1
            report.append({"province":src["province"],"extracted":len(extracted),"added":added,"outcome":"okay" if extracted else "NO_TABLE_DATA"})
        except Exception as e:
            report.append({"province":src["province"],"extracted":0,"added":0,"outcome":type(e).__name__+": "+str(e)[:200]})
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        writer.writerows(sorted(old.values(),key=lambda r:(r["province"],r["year"],r["project_id"],r["title"])))
    report_file=Path("data/provincial_socsc/html_audit.json")
    report_file.parent.mkdir(parents=True,exist_ok=True)
    report_file.write_text(json.dumps({"targets":report,"total_candidate_rows":len(old)},ensure_ascii=False,indent=2),encoding="utf-8")
    print(report_file.read_text(encoding="utf-8"))
if __name__=="__main__":
    main()
