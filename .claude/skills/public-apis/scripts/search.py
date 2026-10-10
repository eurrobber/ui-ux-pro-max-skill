#!/usr/bin/env python3
"""Search the public-apis catalog.

Usage:
  search.py "<query>" [--category CAT] [--no-auth] [--https] [--cors] [-n N]
  search.py --categories
  search.py "<query>" --mcp
"""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score(row, terms):
    name = row["Name"].lower()
    desc = row["Description"].lower()
    cat = row.get("Category", "").lower()
    s = 0
    for t in terms:
        if re.search(rf"\b{re.escape(t)}", name):
            s += 5
        if re.search(rf"\b{re.escape(t)}", cat):
            s += 3
        if re.search(rf"\b{re.escape(t)}", desc):
            s += 2
    return s


def main():
    p = argparse.ArgumentParser(description="Search the public-apis catalog")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--category", "-c", help="Filter by category (substring, case-insensitive)")
    p.add_argument("--no-auth", action="store_true", help="Only APIs that need no key")
    p.add_argument("--https", action="store_true", help="Only HTTPS APIs")
    p.add_argument("--cors", action="store_true", help="Only APIs with CORS enabled (browser-callable)")
    p.add_argument("--mcp", action="store_true", help="Search MCP servers instead of APIs")
    p.add_argument("--categories", action="store_true", help="List categories with counts")
    p.add_argument("-n", type=int, default=10, help="Max results (default 10)")
    a = p.parse_args()

    if a.categories:
        for cat, n in sorted(Counter(r["Category"] for r in load("apis.csv")).items()):
            print(f"{n:4d}  {cat}")
        return

    rows = load("mcp-servers.csv" if a.mcp else "apis.csv")
    if a.category:
        rows = [r for r in rows if a.category.lower() in r.get("Category", "").lower()]
    if a.no_auth:
        rows = [r for r in rows if r["Auth"] == "No"]
    if a.https:
        rows = [r for r in rows if r.get("HTTPS", "Yes") == "Yes"]
    if a.cors:
        rows = [r for r in rows if r.get("CORS") == "Yes"]

    terms = [t for t in re.split(r"\W+", a.query.lower()) if t]
    if terms:
        rows = sorted(((score(r, terms), r) for r in rows), key=lambda x: -x[0])
        rows = [r for s, r in rows if s > 0]

    if not rows:
        print("No results.")
        return
    for r in rows[: a.n]:
        if a.mcp:
            print(f"- {r['Name']} — {r['Description']}\n  {r['URL']}  [auth: {r['Auth']} | transport: {r['Transport']}]")
        else:
            print(f"- {r['Name']} ({r['Category']}) — {r['Description']}\n  {r['URL']}  "
                  f"[auth: {r['Auth']} | https: {r['HTTPS']} | cors: {r['CORS']}]")
    if len(rows) > a.n:
        print(f"... {len(rows) - a.n} more (use -n)")


if __name__ == "__main__":
    main()
