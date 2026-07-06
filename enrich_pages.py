"""
enrich_pages.py — Inject real sheriff/jail data into county HTML pages.

Pages with real data → remove noindex, inject fact box with real info.
Pages without data → keep noindex (thin content, stay hidden from Google).

Usage:
    python enrich_pages.py           # enrich all matched pages
    python enrich_pages.py --dry-run # preview only
"""

import json
import os
import re
import sys
from pathlib import Path

DRY_RUN = "--dry-run" in sys.argv
COUNTIES_DIR = Path("dist/counties")
DATA_FILE    = Path("county_data.json")

FACT_BOX_TEMPLATE = """
<div class="jail-info-box" style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:20px;margin:24px 0;font-size:15px;line-height:1.6">
  <h2 style="margin-top:0;font-size:18px;color:#1a1a2e">{jail_name}</h2>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:6px 0;font-weight:600;width:140px">Address</td><td>{jail_address}</td></tr>
    <tr><td style="padding:6px 0;font-weight:600">Phone</td><td><a href="tel:{jail_phone_raw}">{jail_phone}</a></td></tr>
    <tr><td style="padding:6px 0;font-weight:600">Sheriff / Agency</td><td>{sheriff_name}</td></tr>
    <tr><td style="padding:6px 0;font-weight:600">Inmate Search</td><td><a href="{inmate_search_url}" target="_blank" rel="noopener noreferrer">Official Inmate Roster →</a></td></tr>
  </table>
  {notes_html}
</div>
"""


def county_key(county: str, state: str) -> str:
    return f"{county}|{state}"


def slug_for(county: str, state: str) -> str:
    c = county.lower().replace(" ", "-")
    s = state.lower().replace(" ", "-")
    return f"{c}-county-{s}-inmate-lookup.html"


def build_fact_box(d: dict) -> str:
    phone_raw = re.sub(r"[^\d+]", "", d.get("jail_phone", ""))
    notes_html = ""
    if d.get("notes"):
        notes_html = f'<p style="margin:12px 0 0;color:#555;font-size:14px"><em>{d["notes"]}</em></p>'
    return FACT_BOX_TEMPLATE.format(
        jail_name=d.get("jail_name", "County Jail"),
        jail_address=d.get("jail_address", "—"),
        jail_phone=d.get("jail_phone", "—"),
        jail_phone_raw=phone_raw,
        sheriff_name=d.get("sheriff_name", "—"),
        inmate_search_url=d.get("inmate_search_url", "#"),
        notes_html=notes_html,
    )


def enrich_file(html_path: Path, d: dict) -> tuple[bool, str]:
    html = html_path.read_text(encoding="utf-8")

    # Skip if already enriched
    if "jail-info-box" in html:
        return False, "already enriched"

    fact_box = build_fact_box(d)

    # Inject after first <h1> tag
    if "<h1" in html:
        html = re.sub(r"(</h1>)", r"\1" + fact_box, html, count=1)
    else:
        # Fallback: inject after opening <body>
        html = html.replace("<body>", "<body>" + fact_box, 1)

    # Remove noindex (page now has real content)
    html = html.replace('<meta name="robots" content="noindex, nofollow">\n', "")
    html = html.replace('<meta name="robots" content="noindex, nofollow">', "")

    if not DRY_RUN:
        html_path.write_text(html, encoding="utf-8")

    return True, "enriched"


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Enriching county pages with real data...\n")

    enriched = 0
    skipped  = 0

    for key, d in data.items():
        county = d["county"]
        state  = d["state"]
        slug   = slug_for(county, state)
        path   = COUNTIES_DIR / slug

        if not path.exists():
            print(f"  MISSING  {slug}")
            skipped += 1
            continue

        changed, reason = enrich_file(path, d)
        status = "OK" if changed else "SKIP"
        print(f"  {status:5}  {county} County, {state}  ({reason})")
        if changed:
            enriched += 1
        else:
            skipped += 1

    print(f"\nDone: {enriched} enriched, {skipped} skipped")
    print("Thin pages still noindexed:", 3100 - enriched)
    print("\nNext step: python enrich_pages.py -> redeploy -> submit enriched URLs to GSC")


if __name__ == "__main__":
    main()
