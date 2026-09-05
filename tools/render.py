#!/usr/bin/env python3
"""Render every output from data/cv.json plus the template tree.

This script deliberately knows nothing about what a CV is. It reads three
things and puts them together:

    data/cv.json          the facts        (Notion databases 1-8)
    cv.json["sections"]   the composition  (Notion database 9)
    templates/<target>/   the presentation (this repo)

Adding an output format is adding a directory under templates/ and a Target
value in Notion. It is never editing this file. That separation is the whole
point: the things you change often live where you can change them without a
commit.

Usage
    python tools/render.py --target cv resume web
    python tools/render.py --all --from fixtures/cv.sample.json
    python tools/render.py --target cv_de --photo ~/Pictures/Headshot.jpg
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path

import jinja2

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
BUILD = ROOT / "build"

# Targets that produce a LaTeX document. Everything else is text output
# (markdown, yaml, json) and uses ordinary Jinja delimiters.
TEX_TARGETS = {"cv", "resume", "cv_de"}


# --------------------------------------------------------------------------
# the filter mini-language
# --------------------------------------------------------------------------
# Section rows carry a Filter string like:
#     kind in ("Invited seminar", "Plenary") and scope != "Internal"
#
# This is parsed with ast and walked with an explicit node whitelist. It is
# not eval(): a Notion row can never execute code, which matters because the
# scheduled job runs unattended and a Notion database is a soft target.

_ALLOWED = (
    ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Name, ast.Load, ast.Constant, ast.Tuple, ast.List,
)


class FilterError(ValueError):
    """A Section row's Filter could not be parsed or evaluated."""


def _eval(node, entry: dict):
    if not isinstance(node, _ALLOWED):
        raise FilterError(f"{type(node).__name__} is not allowed in a filter")

    if isinstance(node, ast.Expression):
        return _eval(node.body, entry)

    if isinstance(node, ast.BoolOp):
        vals = [_eval(v, entry) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)

    if isinstance(node, ast.UnaryOp):
        return not _eval(node.operand, entry)

    if isinstance(node, ast.Compare):
        left = _eval(node.left, entry)
        for op, comp in zip(node.ops, node.comparators):
            right = _eval(comp, entry)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.In):
                ok = left in right
            elif isinstance(op, ast.NotIn):
                ok = left not in right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.Gt):
                ok = left > right
            else:
                ok = left >= right
            if not ok:
                return False
            left = right
        return True

    if isinstance(node, (ast.Tuple, ast.List)):
        return [_eval(e, entry) for e in node.elts]

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        # A bare name is a field lookup. Unknown fields are None rather than
        # an error, so a filter mentioning a property you have not filled in
        # yet quietly excludes rather than breaking the build.
        return entry.get(node.id)

    raise FilterError(f"unhandled node {type(node).__name__}")


def passes(expr: str | None, entry: dict) -> bool:
    if not expr or not expr.strip():
        return True
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as exc:
        raise FilterError(f"cannot parse filter {expr!r}: {exc}") from exc
    return bool(_eval(tree, entry))


# --------------------------------------------------------------------------
# LaTeX escaping and small formatting helpers
# --------------------------------------------------------------------------

_TEX_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def tex_escape(value) -> str:
    """Escape text arriving from Notion for LaTeX.

    Every string on the CV passes through here. Without it, one ampersand in
    a venue name breaks a build that nobody is watching.
    """
    if value is None:
        return ""
    out = []
    for ch in str(value):
        out.append(_TEX_MAP.get(ch, ch))
    return "".join(out)


def bold_me(authors: str, surname: str) -> str:
    """Bold the author's own name in an escaped author list.

    Author order is never touched: hep-th lists are alphabetical, so
    reordering would silently claim a seniority that is not there.
    """
    if not authors:
        return ""
    escaped = tex_escape(authors)
    pattern = re.compile(rf"([A-Z]\.(?:\s*[A-Z]\.)*\s*{re.escape(surname)})")
    return pattern.sub(r"\\textbf{\1}", escaped)


def year(value) -> str:
    return str(value)[:4] if value else ""


def daterange(start, end, *, present="present") -> str:
    a, b = year(start), year(end)
    if a and b:
        return a if a == b else f"{a}--{b}"
    if a:
        return f"{a}--{present}"
    return b or ""


# --------------------------------------------------------------------------
# composition
# --------------------------------------------------------------------------

_STATUS_ORDER = ["Published", "Accepted", "Submitted", "Preprint", "In preparation"]
_STATUS_HEADING = {
    "Published": "Published",
    "Accepted": "Accepted",
    "Submitted": "Submitted",
    "Preprint": "Preprints",
    "In preparation": "In preparation",
}

# Talks DB's Kind values, spelled for the entry itself ("Contributed
# talk"); these are the plural section/subsection headings a "kind"
# grouping should show instead — kept here rather than renamed in Notion
# so the entry-level Kind value stays intact for filters elsewhere.
_KIND_ORDER = ["Plenary", "Invited seminar", "Contributed talk", "Poster",
              "Group meeting", "Outreach"]
_KIND_HEADING = {
    "Plenary": "Plenary",
    "Invited seminar": "Invited Seminars",
    "Contributed talk": "Conference Talks",
    "Poster": "Posters",
    "Group meeting": "Group Meetings",
    "Outreach": "Outreach",
}


def sort_entries(entries: list[dict], how: str | None) -> list[dict]:
    how = (how or "date desc").strip()
    if how == "rank":
        return sorted(entries, key=lambda e: (e.get("rank") is None,
                                              e.get("rank") or 0,
                                              e.get("title") or ""))
    reverse = not how.endswith("asc")
    # Ties break on the entry key so a rerun on unchanged data is identical.
    return sorted(entries,
                  key=lambda e: (e.get("date") or "", e.get("key") or ""),
                  reverse=reverse)


def group_entries(entries: list[dict], how: str | None) -> list[dict]:
    how = (how or "none").strip()
    if how == "none" or not how:
        return [{"label": None, "entries": entries}]

    if how == "status":
        buckets = []
        for status in _STATUS_ORDER:
            got = [e for e in entries if e.get("status") == status]
            if got:
                buckets.append({"label": _STATUS_HEADING[status], "entries": got})
        seen = {s for b in buckets for s in [b["label"]]}
        rest = [e for e in entries
                if _STATUS_HEADING.get(e.get("status") or "") not in seen]
        if rest:
            buckets.append({"label": None, "entries": rest})
        return buckets

    if how == "kind":
        buckets: dict[str, list] = {}
        for e in entries:
            buckets.setdefault(e.get("kind") or "", []).append(e)
        ordered = [k for k in _KIND_ORDER if k in buckets]
        ordered += sorted(k for k in buckets if k not in _KIND_ORDER and k)
        out = [{"label": _KIND_HEADING.get(k, k), "entries": buckets[k]} for k in ordered]
        if "" in buckets:
            out.append({"label": None, "entries": buckets[""]})
        return out

    if how == "poster_or_talk":
        posters = [e for e in entries if e.get("kind") == "Poster"]
        talks = [e for e in entries if e.get("kind") != "Poster"]
        out = []
        if talks:
            out.append({"label": "Conference Talks", "entries": talks})
        if posters:
            out.append({"label": "Posters", "entries": posters})
        return out

    if how == "contributed_or_other":
        contributed = [e for e in entries if e.get("kind") == "Contributed talk"]
        other = [e for e in entries if e.get("kind") != "Contributed talk"]
        out = []
        if contributed:
            out.append({"label": "Conference Talks", "entries": contributed})
        if other:
            out.append({"label": "Other Talks", "entries": other})
        return out

    keyfn = {"year": lambda e: year(e.get("date"))}[how]
    buckets: dict[str, list] = {}
    for e in entries:
        buckets.setdefault(keyfn(e), []).append(e)
    return [{"label": k or None, "entries": v}
            for k, v in sorted(buckets.items(), reverse=True)]


def compose(cv: dict, target: str) -> list[dict]:
    """Turn the Sections table into a list of ready-to-render blocks."""
    out = []
    sections = sorted(
        (s for s in cv.get("sections", []) if target in (s.get("targets") or [])),
        key=lambda s: (s.get("order") if s.get("order") is not None else 1e9,
                       s.get("title") or ""),
    )
    for s in sections:
        source = s.get("source")
        if source == "static":
            if not (s.get("body") or "").strip() and not s.get("show_if_empty"):
                continue
            out.append({"title": s.get("title"), "kind": "static",
                        "body": s.get("body") or "",
                        "heading_style": s.get("heading_style") or "section"})
            continue

        pool = [e for e in cv.get(source, []) if (e.get("flags") or {}).get(target)]
        try:
            kept = [e for e in pool if passes(s.get("filter"), e)]
        except FilterError as exc:
            raise SystemExit(
                f"section {s.get('title')!r}: {exc}\n"
                f"Fix the Filter value in Notion database 9."
            ) from exc

        if not kept and not s.get("show_if_empty"):
            continue  # Featured publications lives here until you tick one.

        groups = group_entries(sort_entries(kept, s.get("sort")), s.get("group_by"))
        out.append({"title": s.get("title"), "kind": "entries", "groups": groups,
                    "partial": s.get("partial") or "partials/generic",
                    "heading_style": s.get("heading_style") or "section"})
    return out


# --------------------------------------------------------------------------
# environments
# --------------------------------------------------------------------------

def make_env(target: str, person: dict) -> jinja2.Environment:
    common = dict(
        loader=jinja2.FileSystemLoader(str(TEMPLATES)),
        # Deliberately not StrictUndefined: a missing field is normal here
        # (a talk with no slides, a position with no end date) and should
        # render as nothing, not abort a build nobody is watching.
        undefined=jinja2.Undefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    if target in TEX_TARGETS:
        # {{ }} and {% %} are both valid LaTeX, so the delimiters move.
        env = jinja2.Environment(
            variable_start_string=r"\VAR{", variable_end_string="}",
            block_start_string=r"\BLOCK{", block_end_string="}",
            comment_start_string=r"\#{", comment_end_string="}",
            autoescape=False, **common)
        env.filters["tex"] = tex_escape
        env.filters["authors"] = lambda a: bold_me(a, person.get("surname", "Aretz"))
    else:
        env = jinja2.Environment(autoescape=False, **common)
        env.filters["tex"] = lambda v: v if v is not None else ""
        env.filters["authors"] = lambda a: a or ""
    env.filters["year"] = year
    env.globals["daterange"] = daterange
    return env


# --------------------------------------------------------------------------
# targets
# --------------------------------------------------------------------------

def render_tex(target: str, cv: dict, photo: str | None) -> Path:
    env = make_env(target, cv["person"])
    tpl = env.get_template(f"{target}/document.tex.j2")
    BUILD.mkdir(exist_ok=True)

    photo_name = None
    if photo:
        src = Path(photo).expanduser()
        if not src.is_file():
            raise SystemExit(f"--photo: no such file: {src}")
        photo_name = f"photo{src.suffix.lower()}"
        shutil.copyfile(src, BUILD / photo_name)

    out = BUILD / f"{target}.tex"
    out.write_text(tpl.render(cv=cv, person=cv["person"],
                              sections=compose(cv, target),
                              photo=photo_name), encoding="utf-8")
    return out


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:60] or "untitled"


def render_web(cv: dict) -> list[Path]:
    """Regenerate the Jekyll collections and the CV data file.

    Delete-then-write, not merge: unticking On Web in Notion has to actually
    remove the page. A merge would orphan it and nobody would notice.
    """
    env = make_env("web", cv["person"])
    written = []

    for source, folder, tpl_name in (
        ("publications", "_publications", "web/publication.md.j2"),
        ("talks", "_talks", "web/talk.md.j2"),
    ):
        target_dir = ROOT / folder
        target_dir.mkdir(exist_ok=True)
        for stale in target_dir.glob("*.md"):
            stale.unlink()
        tpl = env.get_template(tpl_name)
        for e in sort_entries([x for x in cv.get(source, [])
                               if (x.get("flags") or {}).get("web")], "date desc"):
            # Use the stored slug, not a fresh slugify of the title: the
            # filename and the permalink must agree, and the slug is what
            # keeps /publication/Keldysh working when a title is reworded.
            slug = e.get("slug") or slugify(e.get("title"))
            name = f"{(e.get('date') or '0000-00-00')}-{slug}.md"
            path = target_dir / name
            path.write_text(tpl.render(entry=e, person=cv["person"]), encoding="utf-8")
            written.append(path)

    data = ROOT / "_data" / "cv.json"
    data.parent.mkdir(exist_ok=True)
    data.write_text(env.get_template("web/cv.json.j2").render(
        cv=cv, person=cv["person"], sections=compose(cv, "web")), encoding="utf-8")
    written.append(data)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", nargs="+", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--from", dest="src", default=str(ROOT / "data" / "cv.json"))
    ap.add_argument("--photo", default=None,
                    help="path to a portrait; templates guard on it, so "
                         "omitting it renders every target photoless")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_file():
        raise SystemExit(f"no data file at {src} — run `make cv-json` first")
    cv = json.loads(src.read_text(encoding="utf-8"))

    with open(ROOT / "tools" / "config.toml", "rb") as fh:
        cfg = tomllib.load(fh)
    cv.setdefault("person", {}).update(
        {k: v for k, v in cfg["person"].items() if k not in cv["person"]})

    targets = args.target
    if args.all or not targets:
        targets = sorted({t for s in cv.get("sections", [])
                          for t in (s.get("targets") or [])})

    # Reproducible PDFs: an unchanged rebuild should produce an empty diff.
    if cv.get("generated") and "SOURCE_DATE_EPOCH" not in os.environ:
        import datetime as _dt
        stamp = _dt.datetime.fromisoformat(cv["generated"].replace("Z", "+00:00"))
        os.environ["SOURCE_DATE_EPOCH"] = str(int(stamp.timestamp()))

    for target in targets:
        if target == "web":
            paths = render_web(cv)
            print(f"web      -> {len(paths)} files")
        else:
            print(f"{target:8} -> {render_tex(target, cv, args.photo).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
