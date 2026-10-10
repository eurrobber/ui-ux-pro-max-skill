#!/usr/bin/env python3
"""Rebuild data/*.csv from the public-apis README.

Usage: python3 update.py [README.md]   (downloads from GitHub when no path is given)
"""
import csv
import re
import sys
import urllib.request
from pathlib import Path

README_URL = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LINK = re.compile(r"^\[(.+?)\]\((.+?)\)$")
STRIP_UTM = re.compile(r"[?&]utm_[^#]*")


def cells(line):
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return [c for c in parts if c != ""] if len(parts) > 5 else parts


def clean(value):
    return value.replace("`", "").strip()


def parse(text):
    apis, mcp = [], []
    section = None
    for line in text.splitlines():
        if line.startswith("## MCP Servers"):
            section = "MCP"
        elif line.startswith("### "):
            section = line[4:].strip()
        elif line.startswith("## "):
            section = None
        if not line.startswith("| [") or section in (None, "APIs Covered Under APILayer Suite!"):
            continue
        row = cells(line)
        m = LINK.match(row[0])
        if not m:
            continue
        name, url = m.group(1), STRIP_UTM.sub("", m.group(2))
        if section == "MCP" and len(row) >= 4:
            mcp.append([name, url, row[1], clean(row[2]), clean(row[3])])
        elif section != "MCP" and len(row) >= 5:
            apis.append([section, name, url, row[1], clean(row[2]), clean(row[3]), clean(row[4])])
    return apis, mcp


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(README_URL) as r:
            text = r.read().decode("utf-8")
    apis, mcp = parse(text)
    DATA_DIR.mkdir(exist_ok=True)
    write(DATA_DIR / "apis.csv", ["Category", "Name", "URL", "Description", "Auth", "HTTPS", "CORS"], apis)
    write(DATA_DIR / "mcp-servers.csv", ["Name", "URL", "Description", "Auth", "Transport"], mcp)
    print(f"{len(apis)} APIs, {len(mcp)} MCP servers -> {DATA_DIR}")


if __name__ == "__main__":
    main()
