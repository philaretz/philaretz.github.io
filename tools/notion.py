#!/usr/bin/env python3
"""Thin Notion client for the CV pipeline.

Notion-Version 2025-09-03 moved schema and rows out from under databases:
a database now only *lists* its data sources, and rows are queried at
/v1/data_sources/{id}/query. Anything written before that release points at
/v1/databases/{id}/query, which is the wrong endpoint now — hence this file
rather than a copied snippet.

Needs NOTION_TOKEN in the environment (an internal integration token, with
the CV page shared to that integration).
"""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.request
import json

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"


class NotionError(RuntimeError):
    pass


def _token() -> str:
    tok = os.environ.get("NOTION_TOKEN")
    if not tok:
        raise NotionError(
            "NOTION_TOKEN is not set.\n"
            "Create an internal integration at notion.so/my-integrations, "
            "share the CV page with it, and export the token."
        )
    return tok


def request(method: str, path: str, body: dict | None = None, *, retries: int = 4):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {_token()}")
    req.add_header("Notion-Version", VERSION)
    req.add_header("Content-Type", "application/json")

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            # 429 and 5xx are transient. Everything else is a real mistake
            # and retrying just hides it.
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise NotionError(f"{method} {path} -> {exc.code}: "
                              f"{exc.read().decode()[:400]}") from exc
    raise NotionError(f"{method} {path}: exhausted retries")


def query_all(data_source_id: str) -> list[dict]:
    """Every row in a data source, following pagination.

    Pagination matters more than it looks: a silently truncated first page
    would drop publications off the CV with no error anywhere.
    """
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        page = request("POST", f"/data_sources/{data_source_id}/query", body)
        rows.extend(page.get("results", []))
        if not page.get("has_more"):
            return rows
        cursor = page["next_cursor"]


# --------------------------------------------------------------------------
# property unwrapping
# --------------------------------------------------------------------------

def plain(prop: dict | None):
    """Notion property -> plain Python value."""
    if not prop:
        return None
    t = prop.get("type")
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in prop[t]) or None
    if t == "select":
        return (prop[t] or {}).get("name")
    if t == "multi_select":
        return [x["name"] for x in prop[t]]
    if t == "checkbox":
        return bool(prop[t])
    if t == "number":
        return prop[t]
    if t in ("url", "email", "phone_number"):
        return prop[t]
    if t == "date":
        return (prop[t] or {}).get("start")
    if t == "relation":
        return [x["id"] for x in prop[t]]
    if t == "formula":
        f = prop[t]
        return f.get(f.get("type"))
    return None


def props(page: dict) -> dict:
    return {name: plain(prop) for name, prop in page.get("properties", {}).items()}


def text(value: str | None) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": value}}]} if value else {"rich_text": []}


def title(value: str) -> dict:
    return {"title": [{"type": "text", "text": {"content": value or ""}}]}


def select(value: str | None) -> dict:
    return {"select": {"name": value} if value else None}


def date(value: str | None) -> dict:
    return {"date": {"start": value} if value else None}


def number(value) -> dict:
    return {"number": value}


def url(value: str | None) -> dict:
    return {"url": value or None}


def checkbox(value: bool) -> dict:
    return {"checkbox": bool(value)}
