#!/usr/bin/env python3
"""Fail if county pages look like doorway spam (Google search "official" links, etc.)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "counties"


def scan(dist: Path = DIST) -> dict:
    pages = sorted(dist.glob("*.html")) if dist.exists() else []
    goog = []
    noindex = []
    for p in pages:
        t = p.read_text(encoding="utf-8", errors="replace")
        if re.search(r"google\.com/search|google\.com/url|bing\.com/search", t, re.I):
            goog.append(p.name)
        if re.search(r"noindex", t, re.I) and re.search(r"name=[\"']robots[\"']", t, re.I):
            noindex.append(p.name)
    return {
        "pages": len(pages),
        "google_search_count": len(goog),
        "google_search_samples": goog[:20],
        "noindex_count": len(noindex),
        "ok": len(goog) == 0 and len(pages) > 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dist", default=str(DIST))
    args = ap.parse_args()
    res = scan(Path(args.dist))
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(
            f"pages={res['pages']} google_search={res['google_search_count']} "
            f"noindex_robots={res['noindex_count']} ok={res['ok']}"
        )
        if res["google_search_samples"]:
            print("samples:", ", ".join(res["google_search_samples"][:10]))
    if res["pages"] == 0:
        print("FAIL: no county pages", file=sys.stderr)
        return 2
    if res["google_search_count"] > 0:
        print("FAIL: google/bing search URLs present in county HTML", file=sys.stderr)
        return 1
    print("PASS quality_gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
