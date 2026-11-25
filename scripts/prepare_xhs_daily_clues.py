#!/usr/bin/env python3
"""Publish only explicitly authorized, manually curated research metadata.
No network access, browser automation, scraping, credentials or note-body export.
"""
import argparse, csv, json, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ACCOUNTS={"Kenny思享","大山经管资料","iiiiop","土豆学姐（研究ing）"}
ROOT=Path(__file__).resolve().parents[1]
TZ=timezone(timedelta(hours=8))

def build():
    src=ROOT/"data/xhs/daily_approved_clues.csv"
    if not src.is_file():
        raise SystemExit("BLOCKED: missing authorized curated input; nothing published")
    now=datetime.now(TZ)
    records={}
    rejected=0
    with src.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            try:
                if row.get("allow_collect")!="yes" or row.get("allow_public_share")!="yes" or not row.get("authorization_reference","").strip():
                    raise ValueError("permission absent")
                author=row["account"].strip()
                if author not in ACCOUNTS:
                    raise ValueError("unverified account")
                dt=datetime.fromisoformat(row["published_at"].replace("Z","+00:00"))
                if dt.tzinfo is None: dt=dt.replace(tzinfo=TZ)
                if not now-timedelta(days=7)<=dt<=now: raise ValueError("outside recent window")
                u=urlsplit(row["source_url"].strip())
                if u.scheme!="https" or u.netloc not in {"www.xiaohongshu.com","xiaohongshu.com"} or not re.fullmatch(r"/(?:explore|discovery/item)/[0-9a-fA-F]{24}",u.path):
                    raise ValueError("not canonical note URL")
                concept=row["concept"].strip()
                if not concept or len(concept)>40 or "\n" in concept or re.search(r"https?://|@|[0-9]{7,}",concept):
                    raise ValueError("not short research concept")
                url="https://www.xiaohongshu.com"+u.path
                key=(url,concept)
                records[key]={"account":author,"published_at":dt.isoformat(),"source_url":url,"concept":concept,"status":"authorized_curated_clue_not_independently_verified"}
            except (ValueError,KeyError,TypeError):
                rejected+=1
    if not records:
        raise SystemExit(f"BLOCKED: 0 eligible records; rejected={rejected}; previous snapshot not overwritten")
    payload={"generated_at":now.isoformat(),"count":len(records),"rejected":rejected,"records":sorted(records.values(),key=lambda r:(r["published_at"],r["source_url"],r["concept"]))}
    out=ROOT/"sources/xhs_daily/latest.json"
    if out.exists():
        previous=json.loads(out.read_text(encoding="utf-8"))
        if previous.get("generated_at","")>payload["generated_at"]: raise SystemExit("BLOCKED: newer snapshot exists")
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(out)
    print(f"PREPARED={len(records)} REJECTED={rejected}; manual disclosure review required before commit")
if __name__=="__main__":
    build()
