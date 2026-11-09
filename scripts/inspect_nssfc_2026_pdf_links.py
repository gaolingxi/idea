#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect publicly linked National Social Science Fund PDF attachments from a university notice.

Source: https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm
Only ordinary, permitted HTML links and direct PDF downloads. Does not bypass authentication,
robots, CAPTCHA, network blocks, or fetch unverified third-party domains.
All downloaded PDF files and tentative title candidates stay under the CURRENT repository's
data/ directory; no PDF content is committed to a public repository.
"""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from crawl_official_sites import SiteFetcher

PAGE = "https://fgc.suse.edu.cn/2026/1010/c5016a217143/page.htm"
# The SUSE notice directly links four public PDFs on the verified People.cn download host.
# Only the university and that specific download host are allowed.
ALLOWED_HOSTS = ["suse.edu.cn", "download.people.com.cn"]
CATEGORIES = {"重点": "key", "一般": "general", "青年": "young", "西部": "western"}
FIELDS = [
    "project_category", "project_title", "project_id", "principal_investigator",
    "organization", "source_notice_url", "attachment_url", "pdf_page",
    "project_status", "evidence_level", "review_state"
]
HEADER_TITLE = re.compile(r"(?:课题|项目|研究)(?:名[称字]|题目)|名称")
HEADER_ID = re.compile(r"(?:项目|课题)?(?:编号|批准号)")
HEADER_PI = re.compile(r"(?:负责人|申请人|主持人)")
HEADER_ORG = re.compile(r"(?:依托|所在|责任|承担)?单位")

def norm(text):
    return re.sub(r"\s+", "", str(text or "")).strip()

def in_allowed_hosts(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme in ("https", "http") and any(
        host == domain or host.endswith("." + domain) for domain in ALLOWED_HOSTS
    )

def is_pdf_candidate(url, label):
    # Exclude ordinary articles; recognize .pdf?version= or visibly titled PDF links.
    path = urlparse(url).path.lower()
    return path.endswith(".pdf") or ".pdf" in (label or "").lower()

def get_pdf_links(html, notice_url):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for tag in soup.select("a[href], iframe[src], embed[src], object[data]"):
        attr = "href" if tag.name == "a" else "data" if tag.name == "object" else "src"
        href = str(tag.get(attr, "")).strip()
        if not href or href.lower().startswith(("javascript:", "data:", "mailto:")):
            continue
        url = urldefrag(urljoin(notice_url, href))[0]
        label = " ".join(filter(None, (
            tag.get_text(" ", strip=True), tag.get("title", ""), tag.get("download", "")
        )))
        if not is_pdf_candidate(url, label):
            continue
        cats = [k for k in CATEGORIES if k in label]
        found.append({"url": url, "label": norm(label), "category": cats[0] if len(cats) == 1 else "",
                      "permitted_host": in_allowed_hosts(url)})
    return list({x["url"]: x for x in found}.values())

def row_columns(headers):
    cols = {}
    for i, header in enumerate(headers):
        h = norm(header)
        if HEADER_TITLE.search(h) and "单位" not in h and "类别" not in h:
            cols.setdefault("project_title", i)
        if HEADER_ID.search(h):
            cols.setdefault("project_id", i)
        if HEADER_PI.search(h):
            cols.setdefault("principal_investigator", i)
        if HEADER_ORG.search(h):
            cols.setdefault("organization", i)
    return cols if "project_title" in cols else None

def parse_pdf(path, notice_url, attachment_url, category):
    try:
        import pdfplumber
    except ImportError:
        return [], "pdfplumber unavailable"
    output, pages, errors = [], 0, []
    try:
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            carry = None
            for page_no, page in enumerate(pdf.pages, 1):
                for table in page.extract_tables() or []:
                    if not table:
                        continue
                    start, cols = 0, None
                    for i, table_row in enumerate(table[:5]):
                        cand = row_columns(table_row or [])
                        if cand:
                            start, cols = i + 1, cand
                            carry = (len(table_row), cols)
                            break
                    if cols is None and carry and len(table[0]) == carry[0]:
                        cols = carry[1]
                    if cols is None:
                        continue
                    for row in table[start:]:
                        if not row:
                            continue
                        def value(name):
                            j = cols.get(name)
                            return norm(row[j]) if j is not None and j < len(row) else ""
                        title = value("project_title")
                        if not (5 <= len(title) <= 220 and re.search(r"[\u4e00-\u9fff]", title)):
                            continue
                        if HEADER_TITLE.fullmatch(title) or "立项名单" in title:
                            continue
                        output.append({
                            "project_category": category,
                            "project_title": title,
                            "project_id": value("project_id"),
                            "principal_investigator": value("principal_investigator"),
                            "organization": value("organization"),
                            "source_notice_url": notice_url,
                            "attachment_url": attachment_url,
                            "pdf_page": page_no,
                            "project_status": "proposed_publicity_not_formal_award",
                            "evidence_level": "participating_university_forwarding_original_list",
                            "review_state": "pending_official_confirmation_and_spotcheck"
                        })
    except Exception as exc:
        errors.append(type(exc).__name__ + ": " + str(exc)[:120])
    return output, f"pages={pages}; errors={'; '.join(errors) if errors else 'none'}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=PAGE)
    ap.add_argument("--out-dir", default="data/nssfc_2026_suse")
    ap.add_argument("--max-pdfs", type=int, default=4)
    args = ap.parse_args()

    root = Path.cwd().resolve()
    out = Path(args.out_dir).resolve()
    if root != out and root not in out.parents:
        raise SystemExit("Output must be inside the active project folder")
    if not in_allowed_hosts(args.url):
        raise SystemExit("Notice URL host not in SUSE official-domain allowlist")
    out.mkdir(parents=True, exist_ok=True)
    fetch = SiteFetcher(min_delay=2, timeout=16)
    report = {
        "task": "IDEA_NSSFC_2026_PDF_LINKS",
        "source_notice_url": args.url,
        "checked_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "notice_access": "not_checked",
        "pdf_links": [],
        "downloaded_pdfs": 0,
        "extracted_candidate_rows": 0,
        "blocked": [],
        "policy": "No bypass. Proposed award list != formal funded project."
    }
    candidates = []
    try:
        final, body, ctype, enc = fetch.get(args.url, ALLOWED_HOSTS)
        if "html" not in ctype.lower():
            raise ValueError("Notice URL did not return HTML")
        # requests may label Chinese legacy pages incorrectly; BeautifulSoup detects encoding.
        html = body.decode(enc or "utf-8", errors="replace") if (enc and enc.lower() not in ("iso-8859-1", "latin-1")) else body
        links = get_pdf_links(html, final)
        report["notice_access"] = "public_html_accessible"
        report["discovered_pdf_links"] = len(links)
        for item in links:
            record = dict(item, result="pending", pages_or_error="")
            report["pdf_links"].append(record)
            if not item["permitted_host"]:
                record["result"] = "external_domain_requires_separate_official_verification"
                continue
            if report["downloaded_pdfs"] >= args.max_pdfs:
                record["result"] = "max_pdfs_reached"
                continue
            try:
                pdf_url, raw, _, _ = fetch.get(item["url"], ALLOWED_HOSTS)
                if not raw.startswith(b"%PDF"):
                    raise ValueError("Response was not a PDF")
                f = out / (hashlib.sha256(pdf_url.encode()).hexdigest()[:16] + ".pdf")
                f.write_bytes(raw)
                report["downloaded_pdfs"] += 1
                rows, details = parse_pdf(f, args.url, pdf_url, item["category"])
                candidates.extend(rows)
                record["result"] = "downloaded; parsed_rows=" + str(len(rows))
                record["pages_or_error"] = details
            except Exception as exc:
                record["result"] = "blocked_or_failed"
                record["pages_or_error"] = type(exc).__name__ + ": " + str(exc)[:180]
                report["blocked"].append({"url": item["url"], "error": record["pages_or_error"]})
    except Exception as exc:
        report["notice_access"] = "blocked_or_failed"
        report["blocked"].append({"url": args.url, "error": type(exc).__name__ + ": " + str(exc)[:180]})

    # Candidates are in project-local data, not added to formal national grants yet.
    seen = {}
    for row in candidates:
        key = (row["project_category"], row["project_id"] or row["project_title"] + row["principal_investigator"])
        seen[key] = row
    if seen:
        with (out / "nssfc_2026_proposed_candidates.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(seen.values())
    report["extracted_candidate_rows"] = len(seen)
    (out / "link_probe_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
