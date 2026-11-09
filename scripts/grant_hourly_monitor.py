#!/usr/bin/env python3
"""Hourly PUBLIC grant-source notices monitor; project titles are separate.

National NSFC, national social-science fund, provincial social-science fund.
Conservative source-first crawl (strict official hosts, robots, rate limit).
"""
import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from crawl_official_sites import SiteFetcher, date_from, html_data, extract_dates, links, clean

HEADERS=["scheme","province","source_id","source_level","notice_title",
         "notice_url","publication_date","record_status","source_page",
         "first_seen","evidence_scope"]
GRANT=re.compile(r"社科|哲学社会|基金|研究|资助|立项|规划|课题|项目|重大专项|评审结果|名单|指南|通告")
DATE_RE=re.compile(r"20(?:24|25|26)[年./-]\s*(?:0?[1-9]|1[0-2])[月./-]\s*(?:0?[1-9]|[12]\d|3[01])")
NATIONAL=[
 {"id":"national_socsc_annual","scheme":"national_socsc","url":"https://www.nopss.gov.cn/GB/219469/431027/index.html",
  "hosts":["www.nopss.gov.cn"],"source_level":"national_program_office"},
 {"id":"national_socsc_major","scheme":"national_socsc","url":"https://www.nopss.gov.cn/GB/219469/431028/index.html",
  "hosts":["www.nopss.gov.cn"],"source_level":"national_program_office"},
 {"id":"national_socsc_special","scheme":"national_socsc","url":"https://www.nopss.gov.cn/GB/219469/431029/index.html",
  "hosts":["www.nopss.gov.cn"],"source_level":"national_program_office"},
 {"id":"national_socsc_root","scheme":"national_socsc","url":"https://www.nopss.gov.cn/GB/219469/",
  "hosts":["www.nopss.gov.cn"],"source_level":"national_program_office"},
 {"id":"nsfc_management","scheme":"nsfc","url":"https://www.nsfc.gov.cn/p1/2857/3203/glkxbtzgg.html",
  "hosts":["www.nsfc.gov.cn"],"source_level":"national_science_foundation"},
 {"id":"nsfc_application_results","scheme":"nsfc","url":"https://www.nsfc.gov.cn/p1/3431/2025nsqsl.html",
  "hosts":["www.nsfc.gov.cn"],"source_level":"national_science_foundation"},
 {"id":"nsfc_funding_results_2026","scheme":"nsfc","url":"https://www.nsfc.gov.cn/p1/3381/2822/141011.html",
  "hosts":["www.nsfc.gov.cn"],"source_level":"national_science_foundation"}
]

def status(t):
    t=clean(t)
    if re.search(r"结项|验收|中期检查",t):return "closed_or_review"
    if re.search(r"拟立项|立项公示|立项名单公示|拟资助",t):return "proposed"
    if re.search(r"立项名单公布|立项结果公布|正式立项|立项公告|批准资助",t):return "formal_announcement"
    if re.search(r"评审结果|资助结果",t):return "result_notice_not_item_list"
    if re.search(r"征集|申报|申请|指南|招标|推荐|征求意见",t):return "call_or_guidance"
    return "other_notice_not_item_list"

def within(date_s,start,end):
    return bool(date_s and start<=date_s<=end)

def collect_listing(fetcher,src,start,end,now):
    final,body,ctype,enc=fetcher.get(src["url"],src["hosts"])
    if "html" not in ctype.lower():
        raise ValueError("Non-HTML source, not parsed")
    soup,title,content=html_data(body,enc)
    pdate,_,_=extract_dates(soup,content)
    seen={}
    # Detail pages may themselves be formal announcements.
    if src.get("detail",False) and within(pdate,start,end):
        row={"scheme":src["scheme"],"province":src.get("province",""),
             "source_id":src["id"],"source_level":src["source_level"],
             "notice_title":title,"notice_url":final,"publication_date":pdate,
             "record_status":status(title),"source_page":src["url"],
             "first_seen":now,"evidence_scope":"official_notice_page_not_individual_project"}
        seen[final]=row
    for a in soup.find_all("a",href=True):
        label=clean(a.get_text(" ",strip=True) or a.get("title",""))
        if len(label)<6 or len(label)>240 or not GRANT.search(label):
            continue
        target=a.get("href","")
        # Using the same host-link parser with URI normalization.
        from urllib.parse import urljoin,urldefrag
        child=urldefrag(urljoin(final,target))[0]
        host=urlparse(child).hostname or ""
        if urlparse(child).scheme not in ("https","http") or not any(host==h or host.endswith("."+h) for h in src["hosts"]):
            continue
        # Do not interpret an attachment name as a separate awarded project.
        if child.lower().split("?")[0].endswith((".xlsx",".xls",".pdf",".doc",".docx")):
            continue
        nearby=clean(a.parent.get_text(" ",strip=True))[:250] if a.parent else ""
        localdate=date_from(nearby)
        if localdate and not within(localdate,start,end):
            continue
        row={"scheme":src["scheme"],"province":src.get("province",""),
             "source_id":src["id"],"source_level":src["source_level"],
             "notice_title":label,"notice_url":child,"publication_date":localdate,
             "record_status":status(label),"source_page":src["url"],
             "first_seen":now,"evidence_scope":"list_item_pending_detail_date_verification"}
        seen[child]=row
    return list(seen.values())

def province_sources(file):
    raw=json.loads(Path(file).read_text(encoding="utf-8"))
    for obj in raw["provinces"]:
        url=obj.get("source_url") or ""
        if not url or not obj.get("allowed_hosts"):continue
        if obj["record_status"] in ("discovered_secondary_only","call_only","formal_partial","not_found"):
            # Do not count university partial reports or unverified search results as whole-province coverage.
            continue
        yield {"id":"prov_"+obj["code"],"scheme":"provincial_socsc",
               "province":obj["province"],"source_level":obj["source_level"],
               "url":url,"hosts":obj["allowed_hosts"],"detail":obj["record_status"]!="portal_only"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--prov-registry",default="sources/provincial_socsc_registry.json")
    ap.add_argument("--output",default="public_metadata/grant_source_notices.csv")
    ap.add_argument("--audit",default="data/grant_hourly/grant_source_audit.json")
    ap.add_argument("--delay",type=float,default=1.5)
    args=ap.parse_args()
    today=datetime.now(ZoneInfo("Asia/Tokyo")).date()
    try: start=today.replace(year=today.year-2).isoformat()
    except ValueError:start=today.replace(year=today.year-2,day=28).isoformat()
    end=today.isoformat()
    source_list=NATIONAL+list(province_sources(args.prov_registry))
    fetcher=SiteFetcher(min_delay=args.delay,timeout=16)
    dst=Path(args.output)
    all_rows={}
    if dst.exists():
        with dst.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                if not row.get("publication_date") or row["publication_date"]>=start:
                    all_rows[(row["scheme"],row["notice_url"])]=row
    counts={"nsfc":0,"national_socsc":0,"provincial_socsc":0}
    problems=[]
    visits=[]
    fresh=0
    for src in source_list:
        try:
            candidates=collect_listing(fetcher,src,start,end,end)
            new=0
            for row in candidates:
                # Undated entries are registered as candidate links, not counted in a verified rolling window.
                key=(row["scheme"],row["notice_url"])
                if key not in all_rows:
                    all_rows[key]=row;new+=1;fresh+=1
            counts[src["scheme"]]+=new
            visits.append({"source_id":src["id"],"province":src.get("province",""),
                           "status":"checked","candidates":len(candidates),"new_notices":new})
        except Exception as e:
            problems.append({"source_id":src["id"],"province":src.get("province",""),
                "source_url":src["url"],"reason":type(e).__name__+": "+str(e)[:180]})
            visits.append({"source_id":src["id"],"province":src.get("province",""),
                           "status":"blocked","candidates":0,"new_notices":0})
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("w",encoding="utf-8-sig",newline="") as f:
        out=csv.DictWriter(f,fieldnames=HEADERS);out.writeheader()
        out.writerows(sorted(all_rows.values(),
           key=lambda r:(r["scheme"],r["publication_date"],r["notice_url"]),reverse=True))
    audit=Path(args.audit);audit.parent.mkdir(parents=True,exist_ok=True)
    payload={"date":end,"window_start":start,"registered_sources":len(source_list),
        "successful_sources":len(source_list)-len(problems),
        "blocked_sources":len(problems),"new_notice_links":fresh,"new_by_type":counts,
        "persistent_notice_links":len(all_rows),"visited":visits,"failures":problems,
        "warning":"Notice links are not individual awarded research projects. Undated notices require date verification."}
    audit.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in payload.items() if k not in ("visited","failures")},ensure_ascii=False))
    if problems: print("BLOCKED_SOURCES",json.dumps(problems,ensure_ascii=False))
if __name__=="__main__":
    main()
