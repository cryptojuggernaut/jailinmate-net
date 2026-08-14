#!/usr/bin/env python3
"""
faq_unique_batch.py — Make FAQ blocks county-specific using county_data.json.

For each county page that has real data (address/phone/roster/sheriff):
  - Replace the FAQ <h2>… section with answers that cite local facts
  - Refresh FAQPage JSON-LD to match
  - Never introduce google.com/search links

Usage:
  python faq_unique_batch.py --limit 50
  python faq_unique_batch.py --all
  python faq_unique_batch.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "counties"
DATA = ROOT / "county_data.json"
MARKER = "<!-- faq-unique-batch -->"


def slug(county: str, state: str) -> str:
    return (
        county.lower().replace(" ", "-")
        + "-county-"
        + state.lower().replace(" ", "-")
        + "-inmate-lookup.html"
    )


def clean_url(u: str) -> str:
    u = (u or "").strip()
    low = u.lower()
    if not u or "google.com/search" in low or "bing.com/search" in low:
        return ""
    if not low.startswith("http"):
        return ""
    return u


def build_faq_html(county: str, state: str, cd: dict) -> str:
    jail = cd.get("jail_name") or f"{county} County Jail"
    addr = cd.get("jail_address") or ""
    phone = cd.get("jail_phone") or ""
    sheriff = cd.get("sheriff_name") or f"{county} County Sheriff's Office"
    roster = clean_url(cd.get("inmate_search_url", ""))
    sheriff_url = clean_url(cd.get("sheriff_url", ""))
    doc = clean_url(cd.get("doc_url", ""))

    if roster:
        find_ans = (
            f'<p>Start with the <a href="{roster}">official {county} County inmate roster</a>. '
            f'You can also call {sheriff}'
            + (f" at {phone}" if phone else "")
            + ". Online records often lag booking by a few hours.</p>"
        )
    else:
        find_ans = (
            f"<p>There is no verified public online roster URL on file for {county} County. "
            f"Call {sheriff}"
            + (f" at {phone}" if phone else "")
            + (
                f' or visit <a href="{sheriff_url}">{sheriff}</a>'
                if sheriff_url
                else ""
            )
            + ". We do not treat web-search results as official jail records.</p>"
        )

    visit_extra = f" The main facility listed is {jail}"
    if addr:
        visit_extra += f" at {addr}"
    visit_extra += "."

    money_ans = (
        f"<p>Ask {jail} which commissary vendor they use (often JPay, Securus, or Access Corrections)"
        + (f" when you call {phone}" if phone else "")
        + ". Limits and fees vary by facility — confirm before sending money.</p>"
    )

    doc_line = (
        f'<a href="{doc}">{state} Department of Corrections</a>'
        if doc
        else f"the {state} Department of Corrections"
    )

    return f"""{MARKER}
<h2>Frequently Asked Questions — {county} County Inmate Lookup</h2>

<h3>How do I find out if someone is in {county} County jail?</h3>
{find_ans}

<h3>What is the phone number for {jail}?</h3>
<p>{"Contact " + sheriff + " at <strong>" + phone + "</strong>." if phone else "Call " + sheriff + " for the current detention desk number."}
{" Facility address on file: " + addr + "." if addr else ""}</p>

<h3>How long does booking take in {county} County?</h3>
<p>Booking commonly takes 2–8 hours depending on volume at {jail}. Weekends and holidays can delay when a name appears in any published system. If urgent, call the facility directly rather than waiting on a website refresh.</p>

<h3>Can I visit an inmate at {county} County jail?</h3>
<p>Usually yes if the person is eligible and the facility is accepting visits.{visit_extra}
Bring government photo ID and confirm hours and dress code with {sheriff} before you go. Video visitation may be offered.</p>

<h3>What if the person is not listed in the county system?</h3>
<p>They may have been released, transferred, or booked under a different name spelling. Check {doc_line}
and the <a href="https://www.bop.gov/inmateloc/">Federal BOP locator</a> for federal custody. Then call {sheriff} to confirm.</p>

<h3>How do I send money to someone at {jail}?</h3>
{money_ans}
"""


def build_faq_schema(county: str, state: str, cd: dict) -> list[dict]:
    jail = cd.get("jail_name") or f"{county} County Jail"
    phone = cd.get("jail_phone") or "the sheriff office"
    addr = cd.get("jail_address") or "the county detention facility"
    return [
        {
            "@type": "Question",
            "name": f"How do I find out if someone is in {county} County jail?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"Use the official {county} County roster if published, or call {cd.get('sheriff_name', 'the sheriff')} at {phone}.",
            },
        },
        {
            "@type": "Question",
            "name": f"What is the phone number for {jail}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"{phone}. Address on file: {addr}.",
            },
        },
        {
            "@type": "Question",
            "name": f"Can I visit an inmate at {county} County jail?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"Contact {jail} for visitation rules. Main location on file: {addr}.",
            },
        },
    ]


def patch_html(html: str, faq_html: str, schema_items: list[dict]) -> str:
    # Replace FAQ section from h2 Frequently Asked through next major section or end of main content
    pattern = re.compile(
        r"(?:<!-- faq-unique-batch -->\s*)?<h2>Frequently Asked Questions[\s\S]*?(?=<h2>|</main>|</article>|<!-- related-counties|$)",
        re.I,
    )
    if not pattern.search(html):
        # try insert before </body>
        if "</body>" in html:
            return html.replace("</body>", faq_html + "\n</body>", 1)
        return html

    html = pattern.sub(faq_html + "\n", html, count=1)

    # Update or inject FAQPage schema
    schema_blob = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": schema_items,
    }
    schema_tag = (
        '<script type="application/ld+json">'
        + json.dumps(schema_blob, ensure_ascii=False)
        + "</script>"
    )
    # Replace existing FAQPage block if present
    faq_schema_re = re.compile(
        r'<script type="application/ld\+json">\s*\{[^<]*"@type"\s*:\s*"FAQPage"[^<]*\}</script>',
        re.I,
    )
    if faq_schema_re.search(html):
        html = faq_schema_re.sub(schema_tag, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", schema_tag + "\n</head>", 1)
    return html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    # Prefer counties with real local facts
    items = []
    for key, cd in data.items():
        if "|" not in key:
            continue
        county, state = key.split("|", 1)
        if not (cd.get("jail_address") or cd.get("jail_phone") or cd.get("inmate_search_url")):
            continue
        items.append((county, state, cd))

    items.sort(key=lambda x: (x[1], x[0]))
    if not args.all:
        items = items[: args.limit]

    updated = skipped = missing = 0
    for county, state, cd in items:
        path = DIST / slug(county, state)
        if not path.exists():
            missing += 1
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        if MARKER in html and not args.all:
            skipped += 1
            continue
        faq_html = build_faq_html(county, state, cd)
        schema = build_faq_schema(county, state, cd)
        new_html = patch_html(html, faq_html, schema)
        if "google.com/search" in new_html:
            print(f"REFUSE google link would appear: {path.name}")
            continue
        if args.dry_run:
            print(f"DRY {path.name}")
            updated += 1
            continue
        path.write_text(new_html, encoding="utf-8")
        updated += 1
        print(f"OK {path.name}")

    print(
        f"Done. updated={updated} skipped={skipped} missing_file={missing} "
        f"candidates={len(items)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
