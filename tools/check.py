#!/usr/bin/env python3
"""Guardrails. Non-zero exit fails the build and blocks the pull request.

Every check here exists because the failure it catches is invisible in the
finished document — the CV still compiles, it is just wrong. That is also why
none of them should be loosened to get a build through: the check passing is
the only evidence anyone has.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def pages(pdf: Path) -> int | None:
    if not pdf.is_file():
        return None
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def main() -> int:
    with open(ROOT / "tools" / "config.toml", "rb") as fh:
        cfg = tomllib.load(fh)
    limits = cfg.get("check", {})
    cv = json.loads((ROOT / "data" / "cv.json").read_text(encoding="utf-8"))

    # 1. The one-pager is one page. The whole point of it, lost to one extra
    #    talk — and it is a judgement call about what earns the space, so it
    #    belongs to Philipp, not to this script.
    limit = limits.get("resume_max_pages", 1)
    n = pages(BUILD / "resume.pdf")
    if n is None:
        fail("resume.pdf missing — did the compile step run?")
    elif n > limit:
        fail(f"resume.pdf is {n} pages, limit {limit}. Untick On Resume on "
             f"something, or raise Rank to push an entry down. Do not shrink "
             f"the margins.")

    # 2. Clean LaTeX. An unescaped & from a Notion field lands here.
    for name in ("cv", "resume"):
        log = BUILD / f"{name}.log"
        if not log.is_file():
            continue
        text = log.read_text(errors="ignore")
        if re.search(r"undefined (control sequence|reference)", text, re.I):
            fail(f"{name}.log has undefined references")
        wide = [float(x) for x in re.findall(r"Overfull \\hbox \(([0-9.]+)pt", text)]
        over = [w for w in wide if w > limits.get("max_overfull_pt", 5.0)]
        if over:
            fail(f"{name}: {len(over)} overfull box(es) over "
                 f"{limits.get('max_overfull_pt', 5.0)}pt (worst {max(over):.1f}pt)")

    # 3. talkmap.py needs a geocodable location or it drops the pin silently.
    for t in cv.get("talks", []):
        if (t.get("flags") or {}).get("web"):
            loc = (t.get("location") or "").strip()
            if not loc:
                fail(f"talk {t['title'][:48]!r} is On Web with no Location")
            elif loc.lower() not in ("online", "virtual") and "," not in loc:
                notes.append(f"talk {t['title'][:40]!r}: location {loc!r} may not "
                             f"geocode — 'City, Country' is what talkmap wants")

    # 4. Half-entered publications must not reach the CV.
    for p in cv.get("publications", []):
        if not (p.get("flags") or {}).get("cv"):
            continue
        if not (p.get("arxiv") or p.get("doi")) and p.get("status") != "In preparation":
            fail(f"publication {p['title'][:48]!r} has no arXiv id and no DOI. "
                 f"Complete it, or set Status = In preparation — never invent one.")

    # 5. The academicpages sample entries must not come back.
    floor = limits.get("min_talk_year", 2024)
    for md in (ROOT / "_talks").glob("*.md"):
        if md.name[:4].isdigit() and int(md.name[:4]) < floor:
            fail(f"{md.name} predates {floor} — the stock sample talks are back. "
                 f"Check that render.py deletes the collection before writing.")

    # 6. Every Sections row must name a template that exists. Without this a
    #    renamed partial makes a whole CV section vanish with no error at all.
    #    Only the LaTeX targets render entries through a partial; the web
    #    target renders sections structurally into _data/cv.json, so a
    #    partial name is meaningless there.
    for s in cv.get("sections", []):
        part = s.get("partial")
        if not part:
            continue
        for target in set(s.get("targets") or []) & {"cv", "resume", "cv_de"}:
            if not (ROOT / "templates" / f"{part}.tex.j2").is_file():
                fail(f"section {s['title']!r} (target {target}) -> "
                     f"templates/{part}.tex.j2 does not exist")

    for note in notes:
        print(f"note:  {note}")
    for f in failures:
        print(f"FAIL:  {f}")
    if not failures:
        print(f"checks passed ({len(notes)} note(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
