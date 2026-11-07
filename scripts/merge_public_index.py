#!/usr/bin/env python3
"""Append-only deduplication of PUBLIC source metadata; never publish raw HTML/PDF."""
import argparse
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

COLS=["source_id","url","category","title","published_date","issued_date",
      "record_type","first_seen","last_seen","record_level"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",default="data/site_crawl/materials.sqlite")
    ap.add_argument("--output",default="public_metadata/official_source_pages.csv")
    args=ap.parse_args()
    today=datetime.now(ZoneInfo("Asia/Tokyo")).date()
    try: start=today.replace(year=today.year-2).isoformat()
    except ValueError: start=today.replace(year=today.year-2,day=28).isoformat()
    now=today.isoformat()
    old={}
    dest=Path(args.output)
    if dest.exists():
        with dest.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                if row["url"] and row.get("published_date","")>=start:
                    old[row["url"]]=row
    db=sqlite3.connect(args.db)
    checked=0
    for source_id,url,cat,title,pub,issued,typ,level in db.execute("""
        SELECT source_id,url,category,title,published_date,issued_date,
               record_type,verified_level FROM documents
    """):
        checked+=1
        if not pub or pub<start or pub>now or not title:
            continue
        if url in old:
            old[url]["last_seen"]=now
        else:
            old[url]={"source_id":source_id,"url":url,"category":cat,
                "title":title,"published_date":pub,"issued_date":issued or "",
                "record_type":typ or "","first_seen":now,"last_seen":now,
                "record_level":"official_source_page_not_individual_project_or_paper"}
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("w",newline="",encoding="utf-8-sig") as f:
        out=csv.DictWriter(f,fieldnames=COLS)
        out.writeheader()
        out.writerows(sorted(old.values(),key=lambda x:(x["published_date"],x["source_id"],x["url"]),reverse=True))
    print(f"SCANNED_DOCUMENT_PAGES={checked} PERSISTED_PUBLIC_METADATA={len(old)} RANGE={start}..{now}")
    print("Individual research titles from PDF / Excel remain UNVERIFIED; never count source pages as research projects.")

if __name__=="__main__":
    main()
