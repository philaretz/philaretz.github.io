#!/usr/bin/env python3
"""INSPIRE-HEP -> Notion Publications.

Queries by BAI, never by name: "a Aretz" will eventually match a homonym and
put someone else's paper on the CV. The BAI cannot.

Rows carry a `Locked` multi-select of property names this script must not
overwrite. That is the entire override mechanism — no special cases in here.
Rows with Source = manual are never touched at all (the delay-orbits paper is
one: INSPIRE does not index it).
"""

from __future__ import annotations

import json
import sys
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notion  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "data" / ".state.json"

FIELDS = ("titles,authors,arxiv_eprints,dois,publication_info,"
          "preprint_date,earliest_date,document_type,control_number")


def fetch(query: str) -> list[dict]:
    url = ("https://inspirehep.net/api/literature?"
           + urllib.parse.urlencode({"q": query, "sort": "mostrecent",
                                     "size": 100, "fields": FIELDS}))
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()).get("hits", {}).get("hits", [])


def initials(name: str) -> str:
    """'Aretz, Philipp Benjamin' -> 'P. B. Aretz' (INSPIRE order preserved)."""
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
    else:
        parts = name.split()
        last, first = parts[-1], " ".join(parts[:-1])
    given = " ".join(f"{w[0]}." for w in first.split() if w)
    return f"{given} {last}".strip()


def normalize(hit: dict) -> dict:
    md = hit.get("metadata", {})
    eprints = md.get("arxiv_eprints") or [{}]
    pub = (md.get("publication_info") or [{}])[0]
    journal = None
    if pub.get("journal_title"):
        vol = pub.get("journal_volume", "")
        year = pub.get("year", "")
        page = pub.get("artid") or pub.get("page_start", "")
        journal = f"{pub['journal_title']} {vol} ({year}) {page}".replace("  ", " ").strip()
    dois = md.get("dois") or []
    return {
        "arxiv": eprints[0].get("value"),
        "primary_class": (eprints[0].get("categories") or [None])[0],
        "title": (md.get("titles") or [{}])[0].get("title"),
        "authors": ", ".join(initials(a["full_name"]) for a in md.get("authors", [])),
        "journal": journal,
        "doi": f"https://doi.org/{dois[0]['value']}" if dois else None,
        "status": "Published" if journal else "Preprint",
        "date": md.get("preprint_date") or (md.get("earliest_date") or "")[:10] or None,
        "control_number": md.get("control_number"),
    }


def key_of(row_props: dict) -> str | None:
    return row_props.get("arXiv") or (
        f"inspire:{row_props['INSPIRE ID']}" if row_props.get("INSPIRE ID") else None)


def main() -> int:
    with open(ROOT / "tools" / "config.toml", "rb") as fh:
        cfg = tomllib.load(fh)
    ds = cfg["notion"]["publications"]
    surname = cfg["person"]["surname"]

    records = [normalize(h) for h in fetch(cfg["inspire"]["query"])]

    # Wrong-author guard. If the BAI ever starts resolving to someone else,
    # this is the line that notices before the CV does.
    strays = [r for r in records if surname.lower() not in (r["authors"] or "").lower()]
    if strays:
        raise SystemExit(
            f"refusing to sync: {len(strays)} INSPIRE record(s) do not list "
            f"{surname} as an author. Check the BAI query.")

    # A failed request must not be able to empty the publication list.
    previous = json.loads(STATE.read_text()) if STATE.is_file() else {}
    before = previous.get("inspire_count")
    if before is not None and len(records) < before:
        raise SystemExit(
            f"refusing to sync: INSPIRE returned {len(records)} records, "
            f"down from {before} last run. Verify by hand at\n"
            f"  https://inspirehep.net/api/literature?q={urllib.parse.quote(cfg['inspire']['query'])}\n"
            f"before concluding a paper was really withdrawn.")

    existing = {}
    for page in notion.query_all(ds):
        p = notion.props(page)
        k = key_of(p)
        if k:
            existing[k] = (page["id"], p)

    created = updated = skipped = 0
    for rec in records:
        k = rec["arxiv"] or f"inspire:{rec['control_number']}"
        payload = {
            "Title": notion.title(rec["title"]),
            "Authors": notion.text(rec["authors"]),
            "arXiv": notion.text(rec["arxiv"]),
            "Primary class": notion.select(rec["primary_class"]),
            "DOI": notion.url(rec["doi"]),
            "Journal": notion.text(rec["journal"]),
            "Status": notion.select(rec["status"]),
            "Date": notion.date(rec["date"]),
            "INSPIRE ID": notion.number(rec["control_number"]),
        }

        if k not in existing:
            notion.request("POST", "/pages", {
                "parent": {"type": "data_source_id", "data_source_id": ds},
                "properties": {**payload,
                               "Source": notion.select("inspire"),
                               "On CV": notion.checkbox(True),
                               "On Resume": notion.checkbox(True),
                               "On Web": notion.checkbox(True)},
            })
            created += 1
            print(f"  + {k}  {rec['title'][:64]}")
            continue

        page_id, p = existing[k]
        if p.get("Source") == "manual":
            skipped += 1
            continue
        locked = set(p.get("Locked") or [])
        patch = {name: val for name, val in payload.items() if name not in locked}
        changed = {n for n in patch
                   if (p.get(n) or None) != (rec.get({
                       "Title": "title", "Authors": "authors", "arXiv": "arxiv",
                       "Primary class": "primary_class", "DOI": "doi",
                       "Journal": "journal", "Status": "status", "Date": "date",
                       "INSPIRE ID": "control_number"}[n]) or None)}
        if changed:
            notion.request("PATCH", f"/pages/{page_id}", {"properties": patch})
            updated += 1
            print(f"  ~ {k}  {', '.join(sorted(changed))}")

    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({"inspire_count": len(records)}, indent=2) + "\n")
    print(f"inspire: {len(records)} records — "
          f"{created} created, {updated} updated, {skipped} manual left alone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
