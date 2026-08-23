#!/usr/bin/env python3
"""Notion databases 1-9 -> data/cv.json.

This is the only place that knows Notion property names. Everything
downstream reads the JSON, which is why the PDF still builds on a plane and
why `git diff data/cv.json` is a readable summary of what a rebuild changed.

Ordering is fixed here (date desc, ties on key) so that rerunning with
unchanged data produces a byte-identical file — an empty diff means nothing
happened, rather than nothing being distinguishable from noise.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cv.json"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:60] or "untitled"


def flags(p: dict) -> dict:
    return {"cv": bool(p.get("On CV")),
            "resume": bool(p.get("On Resume")),
            "web": bool(p.get("On Web"))}


def publications(rows, meetings_by_id=None):
    out = []
    for page in rows:
        p = notion.props(page)
        title = p.get("Title") or ""
        arxiv = p.get("arXiv")
        out.append({
            "key": f"arXiv:{arxiv}" if arxiv else f"notion:{page['id'][:8]}",
            "title": title,
            "slug": p.get("Web slug") or slugify(title),
            "authors": p.get("Authors"),
            "arxiv": arxiv,
            "primary_class": p.get("Primary class"),
            "doi": p.get("DOI"),
            "journal": p.get("Journal"),
            "status": p.get("Status"),
            "date": p.get("Date"),
            "source": p.get("Source"),
            "featured": bool(p.get("Featured")),
            "abstract": p.get("Abstract") or "",
            "slides": p.get("Slides"),
            "bibtex": p.get("BibTeX"),
            "citation": p.get("Citation") or "",
            "rank": p.get("Rank"),
            "flags": flags(p),
        })
    return out


def talks(rows, meeting_titles: dict):
    out = []
    for page in rows:
        p = notion.props(page)
        related = p.get("Event") or []
        out.append({
            "key": f"talk-{page['id'][:8]}",
            "title": p.get("Title") or "",
            "slug": slugify(p.get("Title") or ""),
            "event": meeting_titles.get(related[0]) if related else None,
            "kind": p.get("Kind"),
            "scope": p.get("Scope"),
            "institution": p.get("Institution"),
            "location": p.get("Location"),
            "date": p.get("Date"),
            "slides": p.get("Slides"),
            "recording": p.get("Recording"),
            "abstract": p.get("Abstract") or "",
            "rank": p.get("Rank"),
            "flags": flags(p),
        })
    return out


def simple(rows, title_key: str, extra: dict, date_from: str | None = None):
    """Generic mapper for the databases with no special cases."""
    out = []
    for page in rows:
        p = notion.props(page)
        entry = {"key": f"{title_key.lower()}-{page['id'][:8]}",
                 "title": p.get(title_key) or "",
                 "rank": p.get("Rank"),
                 "flags": flags(p)}
        for dest, src in extra.items():
            entry[dest] = p.get(src)
        if date_from:
            entry["date"] = p.get(date_from)
        out.append(entry)
    return out


def sections(rows):
    out = []
    for page in rows:
        p = notion.props(page)
        out.append({
            "title": p.get("Section") or "",
            "targets": p.get("Target") or [],
            "order": p.get("Order"),
            "source": p.get("Source"),
            "filter": p.get("Filter"),
            "group_by": p.get("Group by") or "none",
            "sort": p.get("Sort"),
            "partial": p.get("Partial"),
            "heading_style": p.get("Heading style") or "section",
            "show_if_empty": bool(p.get("Show if empty")),
            "body": p.get("Body"),
        })
    return sorted(out, key=lambda s: (s["order"] if s["order"] is not None else 1e9,
                                      s["title"]))


def order(entries):
    return sorted(entries, key=lambda e: (e.get("date") or "", e.get("key") or ""),
                  reverse=True)


def main() -> int:
    with open(ROOT / "tools" / "config.toml", "rb") as fh:
        cfg = tomllib.load(fh)
    ds = cfg["notion"]

    raw_meetings = notion.query_all(ds["meetings"])
    meeting_titles = {m["id"]: notion.props(m).get("Name") for m in raw_meetings}

    cv = {
        "generated": dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "Notion CV databases 1-9",
        "person": dict(cfg["person"]),
        "publications": order(publications(notion.query_all(ds["publications"]))),
        "talks": order(talks(notion.query_all(ds["talks"]), meeting_titles)),
        "education": order(simple(
            notion.query_all(ds["education"]), "Institution",
            {"institution": "Institution", "degree": "Degree", "field": "Field",
             "start": "Start", "end": "End", "grade": "Grade", "thesis": "Thesis",
             "advisor": "Advisor", "location": "Location"}, date_from="Start")),
        "positions": order(simple(
            notion.query_all(ds["positions"]), "Role",
            {"role": "Role", "organization": "Organization", "group": "Group",
             "start": "Start", "end": "End", "location": "Location",
             "description": "Description"}, date_from="Start")),
        "awards": order(simple(
            notion.query_all(ds["awards"]), "Name",
            {"awarding_body": "Awarding body", "kind": "Kind", "year": "Year"})),
        "teaching": order(simple(
            notion.query_all(ds["teaching"]), "Course",
            {"role": "Role", "institution": "Institution", "term": "Term",
             "level": "Level", "start": "Start", "end": "End"}, date_from="Start")),
        "service": order(simple(
            notion.query_all(ds["service"]), "Role",
            {"role": "Role", "organization": "Organization", "start": "Start",
             "end": "End", "description": "Description"}, date_from="Start")),
        "meetings": order(simple(
            raw_meetings, "Name",
            {"kind": "Kind", "location": "Location", "start": "Start",
             "end": "End", "contribution": "Contribution"}, date_from="Start")),
        "sections": sections(notion.query_all(ds["sections"])),
    }

    # Awards have a year, not a date; give them one so the shared sort works.
    for a in cv["awards"]:
        if a.get("year") and not a.get("date"):
            a["date"] = f"{int(a['year'])}-01-01"
    cv["awards"] = order(cv["awards"])

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(cv, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = {k: len(v) for k, v in cv.items() if isinstance(v, list)}
    print(f"wrote {OUT.relative_to(ROOT)}: " +
          ", ".join(f"{k} {n}" for k, n in counts.items() if n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
