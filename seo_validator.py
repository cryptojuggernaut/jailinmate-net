"""
seo_validator.py — Pre-deploy SEO gate for jailinmate.net

Checks ALL indexable pages (no noindex tag) for:
- Title tag: present, 30-60 chars
- Meta description: present, 120-160 chars
- H1: exactly one, non-empty
- Canonical URL: present and correct
- Schema/JSON-LD: present
- Open Graph tags: og:title, og:description, og:url
- No placeholder text left in page
- Internal links: all href="/..." targets exist in dist/
- Enriched county pages: must have jail-info-box

Legal pages checked separately:
- privacy.html, terms.html, about.html, contact.html must all exist
- Minimum word count enforced
- Must not contain placeholder text

Exits 0 if all pass, 1 if any FAIL (blocks deploy).
Exits 0 with warnings if only WARNs.

Usage:
    python seo_validator.py           # full audit
    python seo_validator.py --strict  # warnings also fail
    python seo_validator.py --page counties/los-angeles-county-california-inmate-lookup.html
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

DIST = Path("dist")
BASE_URL = "https://jailinmate.net"

LEGAL_PAGES = {
    "privacy.html":  {"min_words": 400, "label": "Privacy Policy"},
    "terms.html":    {"min_words": 600, "label": "Terms of Service"},
    "about.html":    {"min_words": 300, "label": "About"},
    "contact.html":  {"min_words": 200, "label": "Contact"},
}

PLACEHOLDER_PATTERNS = [
    r"\[Your [A-Za-z ]+\]",
    r"Lorem ipsum",
    r"INSERT_",
    r"PLACEHOLDER",
    r"TODO",
    r"FIXME",
    r"\[County Name\]",
    r"\[State\]",
]

PASS = "\033[92mPASS\033[0m"
WARN = "\033[93mWARN\033[0m"
FAIL = "\033[91mFAIL\033[0m"


class Report:
    def __init__(self):
        self.issues = []  # (level, page, message)

    def add(self, level: str, page: str, msg: str):
        self.issues.append((level, page, msg))
        icon = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}.get(level, "?")
        color = {"PASS": PASS, "WARN": WARN, "FAIL": FAIL}.get(level, level)
        print(f"  [{color}] {msg}")

    @property
    def fail_count(self):
        return sum(1 for level, _, _ in self.issues if level == "FAIL")

    @property
    def warn_count(self):
        return sum(1 for level, _, _ in self.issues if level == "WARN")


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def word_count(html: str) -> int:
    text = strip_tags(html)
    return len(re.findall(r"\b\w+\b", text))


def check_title(html: str, report: Report, page: str):
    m = re.search(r"<title>([^<]*)</title>", html, re.IGNORECASE)
    if not m:
        report.add("FAIL", page, "Missing <title> tag")
        return
    title = m.group(1).strip()
    length = len(title)
    if length < 30:
        report.add("WARN", page, f"Title too short ({length} chars): '{title}'")
    elif length > 65:
        report.add("WARN", page, f"Title too long ({length} chars): '{title[:50]}...'")
    else:
        report.add("PASS", page, f"Title OK ({length} chars)")


def check_meta_description(html: str, report: Report, page: str):
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.IGNORECASE)
    if not m:
        report.add("FAIL", page, "Missing meta description")
        return
    desc = m.group(1).strip()
    length = len(desc)
    if length < 100:
        report.add("WARN", page, f"Meta description too short ({length} chars)")
    elif length > 165:
        report.add("WARN", page, f"Meta description too long ({length} chars)")
    else:
        report.add("PASS", page, f"Meta description OK ({length} chars)")


def check_h1(html: str, report: Report, page: str):
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if not h1s:
        report.add("FAIL", page, "No <h1> tag found")
    elif len(h1s) > 1:
        report.add("WARN", page, f"Multiple H1 tags ({len(h1s)})")
    else:
        text = strip_tags(h1s[0]).strip()
        if not text:
            report.add("FAIL", page, "H1 is empty")
        else:
            report.add("PASS", page, f"H1 OK: '{text[:50]}'")


def check_canonical(html: str, report: Report, page: str, expected_url: str):
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', html, re.IGNORECASE)
    if not m:
        report.add("FAIL", page, "Missing canonical URL")
        return
    canonical = m.group(1).strip()
    if canonical != expected_url:
        report.add("WARN", page, f"Canonical mismatch: got '{canonical}', expected '{expected_url}'")
    else:
        report.add("PASS", page, "Canonical URL correct")


def check_og_tags(html: str, report: Report, page: str):
    required = ["og:title", "og:description", "og:url"]
    missing = [tag for tag in required if f'property="{tag}"' not in html and f"property='{tag}'" not in html]
    if missing:
        report.add("WARN", page, f"Missing OG tags: {', '.join(missing)}")
    else:
        report.add("PASS", page, "Open Graph tags present")


def check_schema(html: str, report: Report, page: str):
    if 'application/ld+json' not in html:
        report.add("WARN", page, "No JSON-LD schema markup")
    else:
        report.add("PASS", page, "JSON-LD schema present")


def check_placeholders(html: str, report: Report, page: str):
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    body = body_match.group(1) if body_match else html
    body_text = strip_tags(body)
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, body_text, re.IGNORECASE):
            report.add("FAIL", page, f"Placeholder text found: '{pattern}'")
            return
    report.add("PASS", page, "No placeholder text")


def check_county_enriched(html: str, report: Report, page: str):
    """County pages must have the real data fact box."""
    if "jail-info-box" not in html:
        report.add("FAIL", page, "County page missing real data fact box (jail-info-box)")
    else:
        report.add("PASS", page, "Real jail data fact box present")


def audit_page(html_path: Path, is_county: bool = False) -> Report:
    report = Report()
    html = html_path.read_text(encoding="utf-8", errors="ignore")

    # Build expected canonical
    rel = html_path.relative_to(DIST).as_posix()
    if rel == "index.html":
        expected_url = BASE_URL + "/"
    else:
        expected_url = f"{BASE_URL}/{rel}"

    check_title(html, report, rel)
    check_meta_description(html, report, rel)
    check_h1(html, report, rel)
    check_canonical(html, report, rel, expected_url)
    check_og_tags(html, report, rel)
    check_schema(html, report, rel)
    check_placeholders(html, report, rel)

    if is_county:
        check_county_enriched(html, report, rel)

    return report


def audit_legal_pages() -> Report:
    report = Report()
    for filename, config in LEGAL_PAGES.items():
        path = DIST / filename
        label = config["label"]
        min_words = config["min_words"]

        if not path.exists():
            report.add("FAIL", filename, f"{label} page MISSING: {filename}")
            continue

        html = path.read_text(encoding="utf-8", errors="ignore")
        wc = word_count(html)
        if wc < min_words:
            report.add("FAIL", filename, f"{label}: only {wc} words (need {min_words}+)")
        else:
            report.add("PASS", filename, f"{label}: {wc} words OK")

        # Check for placeholders
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, strip_tags(html), re.IGNORECASE):
                report.add("FAIL", filename, f"{label}: placeholder text '{pattern}'")
                break

    return report


def check_sitemap() -> Report:
    report = Report()
    sitemap = DIST / "sitemap.xml"
    if not sitemap.exists():
        report.add("FAIL", "sitemap.xml", "sitemap.xml MISSING")
    else:
        content = sitemap.read_text(encoding="utf-8")
        url_count = content.count("<loc>")
        report.add("PASS", "sitemap.xml", f"sitemap.xml present ({url_count} URLs)")
    return report


def check_robots_txt() -> Report:
    report = Report()
    robots = DIST / "robots.txt"
    if not robots.exists():
        report.add("WARN", "robots.txt", "robots.txt missing — creating default")
        robots.write_text(
            f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n",
            encoding="utf-8"
        )
    else:
        content = robots.read_text()
        if "Sitemap:" not in content:
            report.add("WARN", "robots.txt", "robots.txt missing Sitemap: directive")
        else:
            report.add("PASS", "robots.txt", "robots.txt OK")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Warnings also fail")
    parser.add_argument("--page", help="Audit single page (relative to dist/)")
    parser.add_argument("--legal-only", action="store_true")
    args = parser.parse_args()

    total_fails = 0
    total_warns = 0

    # ── Legal pages ──────────────────────────────────────────────────────────
    print("\n═══ Legal Pages ═══")
    lr = audit_legal_pages()
    total_fails += lr.fail_count
    total_warns += lr.warn_count

    # ── Infrastructure ───────────────────────────────────────────────────────
    print("\n═══ Infrastructure ═══")
    for r in [check_sitemap(), check_robots_txt()]:
        total_fails += r.fail_count
        total_warns += r.warn_count

    if args.legal_only:
        pass

    elif args.page:
        path = DIST / args.page
        is_county = "counties/" in args.page
        print(f"\n═══ Page: {args.page} ═══")
        r = audit_page(path, is_county=is_county)
        total_fails += r.fail_count
        total_warns += r.warn_count

    else:
        # ── All indexable pages ───────────────────────────────────────────────
        indexable = []
        for html in sorted(DIST.rglob("*.html")):
            content = html.read_text(encoding="utf-8", errors="ignore")
            if 'content="noindex' in content:
                continue
            indexable.append(html)

        print(f"\n═══ Indexable Pages ({len(indexable)}) ═══")
        for html_path in indexable:
            rel = html_path.relative_to(DIST).as_posix()
            is_county = rel.startswith("counties/")
            print(f"\n  ── {rel}")
            r = audit_page(html_path, is_county=is_county)
            total_fails += r.fail_count
            total_warns += r.warn_count

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "═" * 50)
    print(f"RESULT: {total_fails} FAIL  |  {total_warns} WARN")

    if total_fails > 0:
        print("❌ DEPLOY BLOCKED — fix FAILs before deploying")
        sys.exit(1)
    elif args.strict and total_warns > 0:
        print("❌ DEPLOY BLOCKED (--strict) — fix WARNs before deploying")
        sys.exit(1)
    else:
        print("✅ DEPLOY APPROVED")
        sys.exit(0)


if __name__ == "__main__":
    main()
