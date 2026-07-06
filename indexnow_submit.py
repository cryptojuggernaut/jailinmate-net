"""
indexnow_submit.py — Submit enriched URLs to IndexNow (Bing/Yandex instant indexing).

Only submits pages WITHOUT noindex tag (the enriched ones).
Creates indexnow key file in dist/ if needed.

Usage: python indexnow_submit.py
"""

import hashlib
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL  = "https://jailinmate.net"
DIST      = Path("dist")
KEY_FILE  = DIST / "jailinmate-indexnow.txt"
# Use a stable key derived from the domain
INDEXNOW_KEY = hashlib.md5(b"jailinmate.net-indexnow-2024").hexdigest()

INDEXNOW_API = "https://api.indexnow.org/indexnow"


def get_indexable_urls() -> list[str]:
    """Find all HTML files in dist/ that do NOT have noindex."""
    urls = []
    for html in DIST.rglob("*.html"):
        content = html.read_text(encoding="utf-8", errors="ignore")
        if 'content="noindex' in content:
            continue
        # Build URL
        rel = html.relative_to(DIST).as_posix()
        if rel == "index.html":
            url = BASE_URL + "/"
        else:
            url = f"{BASE_URL}/{rel}"
        urls.append(url)
    return sorted(urls)


def ensure_key_file():
    KEY_FILE.write_text(INDEXNOW_KEY, encoding="utf-8")
    print(f"Key file: {KEY_FILE}")


def submit_to_indexnow(urls: list[str]) -> bool:
    payload = json.dumps({
        "host": "jailinmate.net",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{BASE_URL}/{KEY_FILE.name}",
        "urlList": urls
    }).encode("utf-8")

    req = urllib.request.Request(
        INDEXNOW_API,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"IndexNow response: {resp.status} {resp.reason}")
            return resp.status in (200, 202)
    except urllib.error.HTTPError as e:
        print(f"IndexNow HTTP error: {e.code} {e.reason}")
        body = e.read().decode()
        print(f"Body: {body[:300]}")
        return False
    except Exception as e:
        print(f"IndexNow error: {e}")
        return False


def main():
    ensure_key_file()

    urls = get_indexable_urls()
    print(f"Indexable URLs (no noindex): {len(urls)}")
    for u in urls:
        print(f"  {u}")

    if not urls:
        print("Nothing to submit.")
        return

    print(f"\nSubmitting {len(urls)} URLs to IndexNow...")
    ok = submit_to_indexnow(urls)
    print("Success!" if ok else "Failed — check output above")
    print(f"\nNote: Deploy {KEY_FILE.name} to Cloudflare Pages before Bing validates.")


if __name__ == "__main__":
    main()
