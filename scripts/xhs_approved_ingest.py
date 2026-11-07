#!/usr/bin/env python3
"""Xiaohongshu research importer / approved public-page metadata check.
No login, cookie retrieval, reverse-engineered APIs, CAPTCHA bypass or proxy rotation.
"""
import argparse
import csv
import hashlib
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

UA = "ResearchMetadataIndexer/1.0"
ALLOWED = {"xiaohongshu.com", "www.xiaohongshu.com"}
DB = "data/xhs/raw_notes.sqlite"


def normalize(url):
    url = urldefrag(str(url or "").strip()).url
    p = urlparse(url)
    if p.scheme not in {"https", "http"} or p.hostname not in ALLOWED:
        raise ValueError("Only direct xiaohongshu.com URLs are accepted")
    return url


def authorization(row):
    if str(row.get("allow_collect", "")).lower() not in {"yes", "true", "1"}:
        raise PermissionError("allow_collect is not yes")
    rights = str(row.get("rights_basis") or "").strip()
    reference = str(row.get("authorization_reference") or "").strip()
    if not rights or not reference:
        raise PermissionError("Missing rights_basis or authorization_reference")
    return rights, reference


def date_scope(published_at):
    if not published_at:
        return "unknown_date"
    try:
        dt = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return "invalid_date"
    now = datetime.now(timezone.utc)
    return "within_24m" if now-timedelta(days=730) <= dt <= now else "outside_24m"


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS xhs_notes(
        note_key TEXT PRIMARY KEY,
        source_url TEXT NOT NULL,
        title TEXT,
        excerpt TEXT,
        published_at TEXT,
        collected_at TEXT NOT NULL,
        search_query TEXT,
        rights_basis TEXT NOT NULL,
        authorization_reference TEXT NOT NULL,
        acquisition TEXT NOT NULL,
        date_scope TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS fetch_audit(
        checked_at TEXT, source_url TEXT, status TEXT, detail TEXT
    );
    """)
    return db


def write_note(db, row, acquisition):
    url = normalize(row["source_url"])
    rights, reference = authorization(row)
    scope = date_scope(row.get("published_at"))
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    db.execute(
        """INSERT OR IGNORE INTO xhs_notes
        (note_key,source_url,title,excerpt,published_at,collected_at,
         search_query,rights_basis,authorization_reference,acquisition,date_scope)
         VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (key, url, row.get("title", ""), row.get("excerpt", ""),
         row.get("published_at", ""), datetime.now(timezone.utc).isoformat(),
         row.get("search_query", ""), rights, reference, acquisition, scope))
    return db.execute("SELECT changes()").fetchone()[0], scope


def record_audit(db, url, status, detail):
    db.execute("INSERT INTO fetch_audit VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), str(url), status, str(detail)[:400]))
    db.commit()


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.title, self.in_title = {}, [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = a.get("property", a.get("name", "")).lower()
            if key in {"og:title","og:description","description","article:published_time"}:
                self.meta[key] = a.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, text):
        if self.in_title:
            self.title.append(text)

    def extract(self):
        return (self.meta.get("og:title") or "".join(self.title).strip(),
                self.meta.get("og:description") or self.meta.get("description",""),
                self.meta.get("article:published_time",""))


def process_import(args):
    db = connect(args.db)
    n, skipped = 0, 0
    with open(args.source, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                if date_scope(row.get("published_at")) != "within_24m":
                    skipped += 1
                    continue
                inserted, scope = write_note(db, row, "authorized_export")
                n += inserted
            except (ValueError, PermissionError, KeyError) as e:
                skipped += 1
                record_audit(db, row.get("source_url",""), "REJECTED", e)
    db.commit()
    db.close()
    print(f"IMPORTED={n} SKIPPED={skipped}")


def process_fetch(args):
    db = connect(args.db)
    added, blocked, undated = 0, 0, 0
    robots = {}
    with open(args.source, encoding="utf-8-sig", newline="") as f:
        for index, row in enumerate(csv.DictReader(f)):
            if index >= max(0,min(args.max_pages,10)):
                break
            url = row.get("source_url", "")
            try:
                authorization(row)
                url = normalize(url)
                p = urlparse(url)
                origin = p.scheme + "://" + p.hostname
                if origin not in robots:
                    robotsurl = origin + "/robots.txt"
                    req = Request(robotsurl, headers={"User-Agent": UA})
                    with urlopen(req,timeout=10) as r:
                        if r.status != 200:
                            raise PermissionError("robots.txt unavailable")
                        rules = r.read(200000).decode("utf-8","replace")
                    robot = RobotFileParser()
                    robot.parse(rules.splitlines())
                    robots[origin] = robot
                if not robots[origin].can_fetch(UA,url):
                    raise PermissionError("robots.txt disallows this URL")
                with urlopen(Request(url, headers={"User-Agent": UA,"Accept":"text/html"}),timeout=12) as r:
                    if r.status != 200 or "text/html" not in r.headers.get("Content-Type",""):
                        raise PermissionError("Not an openly available HTML page")
                    if r.geturl() != url:
                        raise PermissionError("Redirect needs separate permission")
                    body = r.read(400000).decode("utf-8","replace")
                parser = MetaParser()
                parser.feed(body)
                title, description, pubdate = parser.extract()
                if not title:
                    raise ValueError("No public HTML title")
                rec = dict(row, title=title[:500], excerpt=description[:1500],published_at=pubdate)
                inserted, scope = write_note(db,rec,"approved_public_html_metadata")
                added += inserted
                undated += int(scope != "within_24m")
                record_audit(db,url,"METADATA_ONLY",scope)
            except (ValueError,KeyError,PermissionError,HTTPError,URLError,TimeoutError) as e:
                blocked += 1
                record_audit(db,url,"BLOCKED",e)
                print(f"BLOCKED {url}: {type(e).__name__} {e}")
                if isinstance(e, HTTPError) and e.code in (401,403,429):
                    print("STOP: Access restriction; no workaround")
                    break
            time.sleep(max(5,args.delay_seconds))
    db.commit()
    db.close()
    print(f"METADATA_ONLY={added} NOT_24M_VERIFIED={undated} BLOCKED={blocked}")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    sub = cli.add_subparsers(dest="mode",required=True)
    for name in ("import-export","fetch-approved"):
        p = sub.add_parser(name)
        p.add_argument("--source",required=True)
        p.add_argument("--db",default=DB)
        if name == "fetch-approved":
            p.add_argument("--max-pages",type=int,default=10)
            p.add_argument("--delay-seconds",type=float,default=5.0)
    args = cli.parse_args()
    (process_import if args.mode == "import-export" else process_fetch)(args)
