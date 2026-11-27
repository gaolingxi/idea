#!/usr/bin/env python3
"""Publish only explicitly authorized, manually curated Xiaohongshu research metadata
and independently verified public primary-source leads.

No network access, browser automation, scraping, credentials, cookies, or note-body export.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
DEFAULT_REGISTRY = ROOT / "sources" / "xhs_account_registry.json"
DEFAULT_INPUT = ROOT / "data" / "xhs" / "daily_approved_clues.csv"
DEFAULT_PUBLIC_LEADS = ROOT / "data" / "xhs" / "public_clue_leads.csv"
DEFAULT_OUTPUT = ROOT / "sources" / "xhs_daily" / "latest.json"
DEFAULT_PUBLIC_OUTPUT = ROOT / "sources" / "xhs_daily" / "verified_public_leads.json"

CSV_HEADERS = [
    "account",
    "published_at",
    "source_url",
    "concept",
    "topic_category",
    "primary_source_url",
    "allow_collect",
    "allow_public_share",
    "authorization_reference",
]

PUBLIC_LEAD_HEADERS = [
    "discovered_date",
    "topic_category",
    "concept",
    "primary_source_type",
    "primary_source_title",
    "primary_source_url",
    "primary_published_date",
    "related_account_hint",
]


def load_registry(path: Path) -> tuple[dict[str, dict], set[str]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    accounts: dict[str, dict] = {}
    for entry in data.get("accounts", []):
        if entry.get("status") == "active" and entry.get("account"):
            accounts[entry["account"].strip()] = entry
    categories = {c["id"] for c in data.get("topic_categories", []) if c.get("id")}
    return accounts, categories


def init_templates(data_dir: Path) -> list[Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    approved_tpl = data_dir / "daily_approved_clues.template.csv"
    if not approved_tpl.exists():
        with approved_tpl.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        created.append(approved_tpl)

    public_tpl = data_dir / "public_clue_leads.template.csv"
    if not public_tpl.exists():
        with public_tpl.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(PUBLIC_LEAD_HEADERS)
        created.append(public_tpl)

    return created


def sanitize_https_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    u = urlsplit(raw)
    if u.scheme != "https" or not u.netloc:
        raise ValueError("invalid primary_source_url")
    return f"{u.scheme}://{u.netloc}{u.path}"


def validate_concept(text: str) -> str:
    concept = (text or "").strip()
    if (
        not concept
        or len(concept) > 80
        or "\n" in concept
        or "\r" in concept
        or re.search(r"https?://|@|[0-9]{7,}", concept)
    ):
        raise ValueError("not short research concept")
    return concept


def write_atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_approved_clues(
    src: Path,
    registry_path: Path,
    out: Path,
    window_days: int = 14,
    now: datetime | None = None,
) -> dict:
    if not src.is_file():
        raise SystemExit("BLOCKED: missing authorized curated input; nothing published")

    accounts, valid_categories = load_registry(registry_path)
    now = now or datetime.now(TZ)
    records: dict[tuple[str, str], dict] = {}
    rejected = 0
    total_rows = 0

    with src.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            total_rows += 1
            try:
                if (
                    (row.get("allow_collect") or "").strip().lower() != "yes"
                    or (row.get("allow_public_share") or "").strip().lower() != "yes"
                    or not (row.get("authorization_reference") or "").strip()
                ):
                    raise ValueError("permission absent")

                author = (row.get("account") or "").strip()
                if author not in accounts:
                    raise ValueError("unverified account")

                dt_raw = (row.get("published_at") or "").strip()
                dt = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=TZ)
                if not (now - timedelta(days=window_days) <= dt <= now):
                    raise ValueError("outside recent window")

                u = urlsplit((row.get("source_url") or "").strip())
                if (
                    u.scheme != "https"
                    or u.netloc not in {"www.xiaohongshu.com", "xiaohongshu.com"}
                    or not re.fullmatch(r"/(?:explore|discovery/item)/[0-9a-fA-F]{24}", u.path)
                ):
                    raise ValueError("not canonical note URL")

                concept = validate_concept(row.get("concept") or "")
                topic_category = (row.get("topic_category") or "").strip()
                if not topic_category:
                    topic_category = accounts[author].get("primary_category", "uncategorized")
                elif valid_categories and topic_category not in valid_categories:
                    raise ValueError("unknown topic_category")

                primary_source_url = sanitize_https_url(row.get("primary_source_url") or "")
                url = "https://www.xiaohongshu.com" + u.path
                key = (url, concept)
                record = {
                    "account": author,
                    "topic_category": topic_category,
                    "published_at": dt.isoformat(),
                    "source_url": url,
                    "concept": concept,
                    "status": "authorized_curated_clue_not_independently_verified",
                }
                if primary_source_url:
                    record["primary_source_url"] = primary_source_url
                records[key] = record
            except (ValueError, KeyError, TypeError):
                rejected += 1

    if not records:
        raise SystemExit(
            f"BLOCKED: 0 eligible records (total={total_rows}, rejected={rejected}); previous snapshot not overwritten"
        )

    sorted_records = sorted(
        records.values(),
        key=lambda r: (r["published_at"], r["source_url"], r["concept"]),
    )
    payload = {
        "schema_version": "2.0",
        "generated_at": now.isoformat(),
        "window_days": window_days,
        "registry_accounts_active": sorted(accounts.keys()),
        "total_input_rows": total_rows,
        "count": len(sorted_records),
        "rejected": rejected,
        "accounts_covered": sorted({r["account"] for r in sorted_records}),
        "records": sorted_records,
    }

    if out.exists():
        previous = json.loads(out.read_text(encoding="utf-8"))
        if previous.get("generated_at", "") > payload["generated_at"]:
            raise SystemExit("BLOCKED: newer snapshot exists")

    write_atomic_json(out, payload)
    snapshot_path = out.parent / "snapshots" / f"{now.strftime('%Y-%m-%d')}.json"
    write_atomic_json(snapshot_path, payload)
    return payload


def build_public_leads(
    src: Path,
    registry_path: Path,
    out: Path,
    now: datetime | None = None,
) -> dict | None:
    if not src.is_file():
        return None

    _, valid_categories = load_registry(registry_path)
    now = now or datetime.now(TZ)
    records: dict[tuple[str, str], dict] = {}
    rejected = 0
    total_rows = 0

    with src.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            total_rows += 1
            try:
                discovered_date = (row.get("discovered_date") or "").strip()
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", discovered_date):
                    raise ValueError("invalid discovered_date")
                primary_published_date = (row.get("primary_published_date") or "").strip()
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", primary_published_date):
                    raise ValueError("invalid primary_published_date")
                pub_dt = datetime.fromisoformat(primary_published_date).replace(tzinfo=TZ)
                if pub_dt < now - timedelta(days=730) or pub_dt > now + timedelta(days=1):
                    raise ValueError("outside 24m window")

                topic_category = (row.get("topic_category") or "").strip()
                if valid_categories and topic_category not in valid_categories:
                    raise ValueError("unknown topic_category")

                concept = validate_concept(row.get("concept") or "")
                primary_source_type = (row.get("primary_source_type") or "").strip()
                if primary_source_type not in {"policy", "paper", "conference", "grant", "dataset"}:
                    raise ValueError("invalid primary_source_type")

                primary_source_title = (row.get("primary_source_title") or "").strip()
                if not primary_source_title or len(primary_source_title) > 160:
                    raise ValueError("invalid primary_source_title")

                primary_source_url = sanitize_https_url(row.get("primary_source_url") or "")
                if not primary_source_url or "xiaohongshu.com" in primary_source_url:
                    raise ValueError("must point to independent primary source")

                key = (primary_source_url, concept)
                records[key] = {
                    "discovered_date": discovered_date,
                    "topic_category": topic_category,
                    "concept": concept,
                    "primary_source_type": primary_source_type,
                    "primary_source_title": primary_source_title,
                    "primary_source_url": primary_source_url,
                    "primary_published_date": primary_published_date,
                    "related_account_hint": (row.get("related_account_hint") or "").strip(),
                    "status": "public_search_traced_primary_source",
                }
            except (ValueError, KeyError, TypeError):
                rejected += 1

    if not records:
        return None

    sorted_records = sorted(
        records.values(),
        key=lambda r: (r["primary_published_date"], r["primary_source_url"], r["concept"]),
        reverse=True,
    )
    payload = {
        "schema_version": "1.0",
        "generated_at": now.isoformat(),
        "total_input_rows": total_rows,
        "count": len(sorted_records),
        "rejected": rejected,
        "records": sorted_records,
    }
    write_atomic_json(out, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare sanitized daily XHS & public research clues.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--public-leads", type=Path, default=DEFAULT_PUBLIC_LEADS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--public-output", type=Path, default=DEFAULT_PUBLIC_OUTPUT)
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--init-template", action="store_true")
    args = parser.parse_args()

    if args.init_template:
        created = init_templates(args.input.parent)
        print(f"TEMPLATES_READY={len(created)} DIR={args.input.parent}")
        if not args.input.is_file() and not args.public_leads.is_file():
            return

    public_payload = build_public_leads(args.public_leads, args.registry, args.public_output)
    if public_payload:
        print(f"PUBLIC_LEADS_PREPARED={public_payload['count']} REJECTED={public_payload['rejected']}")

    payload = build_approved_clues(
        src=args.input,
        registry_path=args.registry,
        out=args.output,
        window_days=args.window_days,
    )
    print(
        f"PREPARED={payload['count']} REJECTED={payload['rejected']} "
        f"ACCOUNTS={','.join(payload['accounts_covered'])}; manual disclosure review required before commit"
    )


if __name__ == "__main__":
    main()
