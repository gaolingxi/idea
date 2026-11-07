#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source-first research archiver. Index -> article -> official attachment.
No search engines, credentials, bypass, private endpoints or unrestricted spidering.
HTML/PDF data remain local; link records are never mistaken for individual projects.
"""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import time
from collections import deque
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

UA = "EconResearchSourceIndex/1.0 (public pages; low-rate; local academic index)"
DOC_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx")
PERMITTED_SCHEMES = ("https", "http")
DATE = re.compile(r"(?<!\d)(20(?:2[4-9]|3\d))[-./年](0?[1-9]|1[0-2])[-./月](0?[1-9]|[12]\d|3[01])日?")
ISSUED = re.compile(r"(?:成文日期|发文日期|印发日期|签发日期)[：:\s]*([^\n\r]{0,24})")
EFFECTIVE = re.compile(r"(?:自[^\n。；]{0,20}起施行|实施日期[：:\s]*[^\n。]{0,30}|施行日期[：:\s]*[^\n。]{0,30})")
PUBLISHED = re.compile(r"(?:发布时间|发布日期|公开日期)[：:\s]*([^\n\r]{0,24})")
HEADINGS = re.compile(r"项目名称|课题名称|论文题目|项目题目|研究题目")
ACCESS_BLOCKED = {401, 403, 429}


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def normalize(url):
    u = urldefrag(url.strip())[0]
    p = urlparse(u)
    if p.scheme not in PERMITTED_SCHEMES or not p.hostname:
        raise ValueError("Unsupported URL")
    return u


def allowed(url, hosts):
    host = (urlparse(url).hostname or "").lower()
    allowed_hosts = [h.lower() for h in hosts]
    return any(host == h or host.endswith("." + h) for h in allowed_hosts)


def date_from(s):
    m = DATE.search(str(s or ""))
    if not m:
        return ""
    try:
        return date(*map(int, m.groups())).isoformat()
    except ValueError:
        return ""


def classify(title, kind):
    text = clean(title)
    if kind == "conference_paper":
        return "conference_program" if re.search(r"论文|入选|日程|议程|交流", text) else "conference_notice"
    if re.search(r"拟立项|立项公示|公示名单", text):
        return "proposed"
    if re.search(r"立项公告|立项名单|立项结果|批准资助|资助结果", text):
        return "formal_or_reported_award"
    if re.search(r"申请|申报|课题指南|征文|选题征集|招标", text):
        return "call_or_guidance"
    if kind == "policy":
        return "policy_release"
    return "other_announcement"


def db_open(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript("""
      PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS documents(
       source_id TEXT NOT NULL, url TEXT NOT NULL,
       category TEXT NOT NULL, title TEXT NOT NULL,
       published_date TEXT, issued_date TEXT, effective_text TEXT,
       record_type TEXT, archive_path TEXT, captured_at TEXT,
       content_hash TEXT, verified_level TEXT,
       PRIMARY KEY(source_id,url));
      CREATE TABLE IF NOT EXISTS attachments(
       source_id TEXT NOT NULL, url TEXT NOT NULL,
       title TEXT, parent_url TEXT, saved_path TEXT,
       extracted_text_path TEXT, status TEXT, captured_at TEXT,
       PRIMARY KEY(source_id,url));
      CREATE TABLE IF NOT EXISTS extracted_candidates(
       source_id TEXT, parent_url TEXT, attachment_url TEXT,
       page_no INTEGER, candidate_title TEXT,
       review_state TEXT, UNIQUE(source_id,attachment_url,page_no,candidate_title));
      CREATE TABLE IF NOT EXISTS crawl_log(
       source_id TEXT, url TEXT, outcome TEXT, detail TEXT, checked_at TEXT);
    """)
    return db


class SiteFetcher:
    def __init__(self, min_delay=2.0, timeout=15):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.5"})
        self.rules = {}
        self.last = {}
        self.delay = max(1.0, float(min_delay))
        self.timeout = timeout

    def policy(self, url):
        p = urlparse(url)
        origin = p.scheme + "://" + p.netloc
        if origin not in self.rules:
            robots_url = origin + "/robots.txt"
            try:
                r = self.session.get(robots_url, timeout=self.timeout)
            except requests.RequestException as e:
                raise PermissionError("robots retrieval failed: " + str(e)[:100]) from e
            if r.status_code in ACCESS_BLOCKED:
                raise PermissionError("robots access blocked: " + str(r.status_code))
            if r.status_code == 404:
                bot = RobotFileParser()
                bot.parse([])
            elif r.status_code == 200:
                bot = RobotFileParser()
                bot.parse(r.text.splitlines())
            else:
                raise PermissionError("robots unknown status: " + str(r.status_code))
            self.rules[origin] = bot
        return self.rules[origin], origin

    def get(self, url, hosts, max_bytes=12000000):
        url = normalize(url)
        if not allowed(url,hosts):
            raise PermissionError("Outside allowed host")
        bot, origin = self.policy(url)
        if not bot.can_fetch(UA, url):
            raise PermissionError("Disallowed by robots.txt")
        crawl_delay = bot.crawl_delay(UA) or self.delay
        gap = max(self.delay, float(crawl_delay))
        wait = self.last.get(origin, 0.0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last[origin] = time.monotonic()
        response = self.session.get(url,timeout=self.timeout,stream=True,allow_redirects=True)
        if response.status_code in ACCESS_BLOCKED:
            raise PermissionError("HTTP restricted " + str(response.status_code))
        response.raise_for_status()
        if not allowed(response.url, hosts):
            raise PermissionError("Redirect outside allowed hosts")
        chunks, total = [], 0
        for chunk in response.iter_content(65536):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("Response exceeds size limit")
            chunks.append(chunk)
        body = b"".join(chunks)
        content_type = response.headers.get("content-type", "")
        return response.url, body, content_type, response.encoding


def log(db, source_id, url, outcome, detail=""):
    db.execute("INSERT INTO crawl_log VALUES(?,?,?,?,?)",
               (source_id,url,outcome,str(detail)[:500],datetime.utcnow().isoformat()))
    db.commit()


def html_data(body, encoding):
    soup = BeautifulSoup(body, "html.parser", from_encoding=(None if str(encoding).lower() in ("iso-8859-1","latin-1","none") else encoding))
    # Site chrome is excluded where possible; keep full HTML only in local archive.
    for tag in soup.select("script,style,nav,footer,header"):
        tag.decompose()
    h1 = soup.find("h1")
    meta = soup.find("meta",attrs={"property":"og:title"})
    title = clean((h1.get_text(" ",strip=True) if h1 else "") or
                  (meta.get("content","") if meta else "") or
                  (soup.title.get_text(" ",strip=True) if soup.title else ""))
    main = soup.select_one("article, .article, .TRS_Editor, #zoom, .content, #content, main") or soup.body or soup
    text = main.get_text("\n",strip=True)
    return soup,title,text


def extract_dates(soup,text):
    # Publication date is not silently replaced by document issue/effective date.
    top = text[:1400]
    meta = soup.find("meta", attrs={"property":"article:published_time"})
    pub = date_from(meta.get("content","") if meta else "")
    pm = PUBLISHED.search(top)
    if not pub and pm:
        pub = date_from(pm.group(1))
    if not pub:
        pub = date_from(top[:350])
    im = ISSUED.search(top)
    issued = date_from(im.group(1)) if im else ""
    em = EFFECTIVE.search(text[:5000])
    effective = clean(em.group())[:120] if em else ""
    return pub, issued, effective


def links(soup,base,hosts):
    seen = set()
    for a in soup.find_all("a",href=True):
        href = urljoin(base,a["href"])
        href = urldefrag(href)[0]
        if not allowed(href,hosts) or href in seen:
            continue
        seen.add(href)
        label = clean(a.get_text(" ",strip=True) or a.get("title",""))
        yield href,label


def archive(root,source_id,url,body,ext):
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    p = root / "archive" / source_id / (key+ext)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(body)
    return str(p)


def upsert_document(db, src, url, title, pub, issued, eff, typ, local, raw):
    db.execute("""
      INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(source_id,url) DO UPDATE SET
      title=excluded.title,published_date=excluded.published_date,
      issued_date=excluded.issued_date,effective_text=excluded.effective_text,
      record_type=excluded.record_type,archive_path=excluded.archive_path,
      captured_at=excluded.captured_at,content_hash=excluded.content_hash
    """,(src["id"],url,src["category"],title,pub,issued,eff,typ,local,
         datetime.utcnow().isoformat(),hashlib.sha256(raw).hexdigest(),
         "official_source_page_not_individual_title"))
    db.commit()


def parse_pdf_candidates(db, src, parent_url, url, content, root):
    try:
        import pdfplumber
    except ImportError:
        return "", "pdfplumber_missing"
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    pdf_path = root / "archive" / src["id"] / (key+".pdf")
    if not pdf_path.exists():
        pdf_path.parent.mkdir(parents=True,exist_ok=True)
        pdf_path.write_bytes(content)
    text_path = root / "extracted_text" / src["id"] / (key+".txt")
    text_path.parent.mkdir(parents=True,exist_ok=True)
    lines, found = [], 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for no,page in enumerate(pdf.pages,1):
                lines.append("--- PAGE "+str(no)+" ---\n"+(page.extract_text() or ""))
                for table in page.extract_tables() or []:
                    if not table:
                        continue
                    headers = [clean(h) for h in table[0]]
                    col = next((i for i,h in enumerate(headers) if HEADINGS.search(h)),None)
                    if col is None:
                        continue
                    for row in table[1:]:
                        if col >= len(row): continue
                        candidate = clean(row[col])
                        if not 8 <= len(candidate) <= 220 or HEADINGS.fullmatch(candidate): continue
                        db.execute("""INSERT OR IGNORE INTO extracted_candidates
                          VALUES(?,?,?,?,?,?)""",(src["id"],parent_url,url,no,candidate,"needs_row_verification"))
                        found += 1
        text_path.write_text("\n".join(lines),encoding="utf-8")
        db.commit()
    except Exception as e:
        return "", "pdf_parse_error: "+str(e)[:130]
    return str(text_path), "PDF_TABLE_CANDIDATES_"+str(found)


def attachment(db, fetcher, src, parent, url, label, root, max_bytes=12000000):
    key = (src["id"],url)
    if db.execute("SELECT 1 FROM attachments WHERE source_id=? AND url=?",key).fetchone():
        return
    try:
        final,raw,ctype,_ = fetcher.get(url,src["allowed_hosts"],max_bytes=max_bytes)
        ext = Path(urlparse(final).path).suffix.lower()
        if ext not in DOC_SUFFIXES:
            raise ValueError("Not a recognized attachment")
        # Local raw collection only. Never push data/ to public GitHub.
        local = archive(root,src["id"],final,raw,ext)
        textpath,status = ("","stored_unparsed")
        if ext == ".pdf":
            textpath,status = parse_pdf_candidates(db,src,parent,final,raw,root)
        db.execute("INSERT OR REPLACE INTO attachments VALUES(?,?,?,?,?,?,?,?)",
                   (src["id"],final,label,parent,local,textpath,status,datetime.utcnow().isoformat()))
        db.commit()
        log(db,src["id"],url,"ATTACHMENT_STORED",status)
    except Exception as e:
        log(db,src["id"],url,"ATTACHMENT_BLOCKED",e)


def crawl_source(src, fetcher, db, root, since, args):
    max_pages = min(src.get("max_pages",12),args.max_pages)
    listing = src["mode"] == "listing"
    q = deque([(src["url"],0,"seed")])
    # Verified site pagination; do not search the whole internet.
    tpl = src.get("pagination_template","")
    if listing and tpl:
        folder = src["url"].rsplit("/",1)[0]+"/"
        for n in range(1,max_pages):
            q.append((urljoin(folder,tpl.format(n=n)),0,"pagination"))
    visited,details,seen,found = set(),0,0,0
    topic = re.compile(src.get("include_regex","."))
    stop = False
    while q and seen < max_pages+args.max_details:
        url,depth,kind = q.popleft()
        if url in visited or not allowed(url,src["allowed_hosts"]):
            continue
        if depth >= 1 and details >= args.max_details:
            continue
        visited.add(url)
        try:
            url,raw,ctype,enc = fetcher.get(url,src["allowed_hosts"])
            if "html" not in ctype.lower():
                log(db,src["id"],url,"NON_HTML",ctype)
                continue
            soup,title,text = html_data(raw,enc)
            pub,issued,eff = extract_dates(soup,text)
            # An undated listing is retained to discover documents; undated details
            # are kept but flagged instead of counted as verified 24m records.
            in_window = (pub >= since) if pub else False
            local = archive(root,src["id"],url,raw,".html")
            if not listing or kind == "article" or depth >= 1:
                typ=classify(title,src["category"])
                upsert_document(db,src,url,title,pub,issued,eff,typ,local,raw)
                details += 1
                found += int(in_window)
            log(db,src["id"],url,"HTML_SAVED","date="+pub+"; "+kind)
            seen += 1
            if args.attachments:
                for child,label in links(soup,url,src["allowed_hosts"]):
                    if Path(urlparse(child).path).suffix.lower() in DOC_SUFFIXES:
                        attachment(db,fetcher,src,url,child,label,root)
            if not listing and kind != "seed":
                continue
            if not listing:
                continue
            for child,label in links(soup,url,src["allowed_hosts"]):
                ext = Path(urlparse(child).path).suffix.lower()
                if ext in DOC_SUFFIXES:
                    continue
                if child in visited or not child.lower().split("?")[0].endswith((".html",".htm","/")):
                    continue
                if clean(label) in ("下一页","下页","后一页","尾页") and kind in ("seed","pagination"):
                    q.append((child,0,"pagination"))
                elif 8<=len(label)<=240 and topic.search(label) and kind in ("seed","pagination"):
                    q.append((child,1,"article"))
        except PermissionError as e:
            log(db,src["id"],url,"BLOCKED",e)
            if "HTTP restricted" in str(e) or "robots" in str(e):
                stop=True
                break
        except Exception as e:
            log(db,src["id"],url,"ERROR",type(e).__name__+": "+str(e)[:200])
    return {"source_id":src["id"],"pages_checked":seen,"dated_documents_seen":found,
            "status":"blocked" if stop else "finished_with_limits",
            "last_error":""}


def write_csv(db,root):
    p = root/"documents.csv"
    cols = ["source_id","url","category","title","published_date","issued_date",
            "effective_text","record_type","archive_path","captured_at","verified_level"]
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(cols)
        for row in db.execute("SELECT "+",".join(cols)+" FROM documents ORDER BY published_date DESC"):
            w.writerow(row)
    return str(p)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry",default="sources/site_registry.json")
    p.add_argument("--db",default="data/site_crawl/materials.sqlite")
    p.add_argument("--source-id",action="append")
    p.add_argument("--max-pages",type=int,default=5)
    p.add_argument("--max-details",type=int,default=60)
    p.add_argument("--days",type=int,default=731)
    p.add_argument("--delay",type=float,default=2.0)
    p.add_argument("--attachments",action="store_true")
    args=p.parse_args()
    cfg=json.loads(Path(args.registry).read_text(encoding="utf-8"))
    root=Path(args.db).parent
    db=db_open(args.db)
    fetcher=SiteFetcher(args.delay)
    since=(date.today()-__import__("datetime").timedelta(days=args.days)).isoformat()
    results=[]
    for src in cfg["sources"]:
        if args.source_id and src["id"] not in args.source_id: continue
        results.append(crawl_source(src,fetcher,db,root,since,args))
    path=write_csv(db,root)
    report=root/"crawl_summary.json"
    report.write_text(json.dumps({"window_start":since,"window_end":date.today().isoformat(),
         "results":results,"documents_csv":path,"note":"Document records are source pages, not necessarily individual projects or papers; attachment table rows need verification."},
         ensure_ascii=False,indent=2),encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
