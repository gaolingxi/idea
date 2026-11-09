#!/usr/bin/env python3
"""Persist conservative, review-required national social-science/NSFC PDF row candidates.

Only columns detected in official PDFs; NEVER calls overall award numbers titles.
"""
import argparse,csv,sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

FIELDS=["scheme","source_id","source_url","attachment_url","page_number",
        "candidate_project_title","notice_title","notice_status","first_seen",
        "review_state"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",default="data/grant_national/materials.sqlite")
    ap.add_argument("--output",default="public_metadata/national_grant_project_candidates.csv")
    args=ap.parse_args()
    d=Path(args.db)
    out=Path(args.output)
    old={}
    if out.exists():
        with out.open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                old[(r["scheme"],r["attachment_url"],r["candidate_project_title"])]=r
    counts={"national_socsc":0,"nsfc":0}
    if d.exists():
        db=sqlite3.connect(d)
        query="""
          SELECT c.source_id,c.parent_url,c.attachment_url,c.page_no,c.candidate_title,
                 COALESCE(d.title,''),COALESCE(d.record_type,'')
          FROM extracted_candidates c
          LEFT JOIN documents d ON d.source_id=c.source_id AND d.url=c.parent_url
        """
        for sid,parent,attachment,page,title,announcement,typ in db.execute(query):
            scheme="national_socsc" if sid.startswith("project_nopss") else "nsfc" if sid.startswith("project_nsfc") else None
            if not scheme:continue
            if typ not in ("formal_or_reported_award","proposed"):
                # A grant application call, or topic guide, is not a funded project list.
                continue
            if not title.strip():continue
            key=(scheme,attachment,title.strip())
            if key in old:continue
            old[key]={"scheme":scheme,"source_id":sid,"source_url":parent,
                "attachment_url":attachment,"page_number":str(page),
                "candidate_project_title":title.strip(),
                "notice_title":announcement,"notice_status":typ,
                "first_seen":datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat(),
                "review_state":"pending_individual_project_verification"}
            counts[scheme]+=1
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        writer.writerows(sorted(old.values(),key=lambda r:(r["scheme"],r["attachment_url"],r["candidate_project_title"])))
    print({"project_candidates_in_index":len(old),"new_pending_by_category":counts,
           "note":"Pending PDF table rows are not verified formal awards."})
if __name__=="__main__":main()
