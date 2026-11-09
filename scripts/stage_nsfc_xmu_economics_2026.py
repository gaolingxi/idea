#!/usr/bin/env python3
"""Audit XMU Economics 2026 NSFC award table; append only to a NEW staged CSV."""
import csv, io, pathlib, re, sys
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

URL="https://soe.xmu.edu.cn/info/6411/1066315.htm"
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"public_metadata/nsfc_awards_2025_2026_partial.csv"
OUT=ROOT/"data/nsfc_xmu_economics_2026_staged.csv"
def main():
    assert urlparse(URL).hostname=="soe.xmu.edu.cn"
    response=requests.get(URL,timeout=25,headers={"User-Agent":"AcademicPublicSourceAudit/1.0"})
    if response.status_code!=200:
        raise RuntimeError(f"BLOCKED HTTP {response.status_code}; do not bypass")
    response.encoding=response.apparent_encoding
    soup=BeautifulSoup(response.text,"html.parser")
    tables=soup.find_all("table")
    records=[]
    for table in tables:
        for tr in table.find_all("tr"):
            cells=[c.get_text(" ",strip=True) for c in tr.find_all(["td","th"])]
            if len(cells)<6 or not cells[0].isdigit(): continue
            no,pi,title,typ,approval,amount=cells[:6]
            if not (1<=int(no)<=23 and title and pi and approval.isdigit()):continue
            records.append((int(no),pi,title,typ,approval,amount))
    if len(records)!=23 or sorted(r[0] for r in records)!=list(range(1,24)):
        raise RuntimeError(f"BLOCKED: parsed {len(records)} rows, expected 23 consecutive rows")
    if len({r[4] for r in records})!=23: raise RuntimeError("BLOCKED duplicate approval numbers in source")
    with BASE.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; existing=list(reader)
    old_ids={r["approval_number"].strip() for r in existing}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    new=[]
    for no,pi,title,typ,approval,amount in records:
        if approval in old_ids:continue
        row={k:"" for k in fields}
        row.update(scheme="nsfc",award_year="2026",approval_number=approval,project_title=title,
                   principal_investigator=pi,institution="厦门大学",reporting_unit="经济学科",
                   project_type=typ,funding_amount=amount,source_url=URL,
                   source_level="university_published_award_list",
                   collection_scope="partial_institution_records_not_nationwide",
                   publication_date="2026-08-27",
                   review_state=("approval_number_length_anomaly_verify_manually" if len(approval)!=8
                                 else "pending_crosscheck_with_NSFC_public_record"))
        new.append(row)
    with OUT.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(new)
    print(f"staged={len(new)} existing={len(existing)} anomalies="+
          repr([(r["principal_investigator"],r["approval_number"]) for r in new if len(r["approval_number"])!=8]))
    print("No existing public_metadata or frozen NSSFC data modified. Manual audit required before publication.")
if __name__=="__main__": main()
