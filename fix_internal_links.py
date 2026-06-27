"""
fix_internal_links.py — Phase 2.1 of the Google Indexing Fix Plan
Injects a "Related Counties in {State}" section into every county HTML page.

What it does:
  - Reads counties.csv to know which counties are in each state
  - For each county page in dist/counties/, appends 5 same-state county links
    (excluding itself) just before </body>
  - Skips pages already patched (idempotent — safe to re-run)
  - Reports how many pages were updated

Usage:
  python fix_internal_links.py           # patch all county pages
  python fix_internal_links.py --dry-run # count only, no writes
  python fix_internal_links.py --state TX # one state only
"""
import argparse
import csv
import random
import re
from pathlib import Path

DIST_DIR   = Path(__file__).parent / "dist"
COUNTY_DIR = DIST_DIR / "counties"
CSV_PATH   = Path(__file__).parent / "counties.csv"
MARKER     = "<!-- related-counties-injected -->"
N_LINKS    = 6   # number of same-state county links to add


def slug(county: str, state: str) -> str:
    return (
        county.lower().replace(" ", "-")
        + "-county-"
        + state.lower().replace(" ", "-")
        + "-inmate-lookup.html"
    )


def load_counties() -> dict[str, list[tuple[str, str]]]:
    """Returns {state_abbr: [(county, state_full), ...]}"""
    by_state: dict[str, list[tuple[str, str]]] = {}
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            abbr = row["state_abbr"].strip()
            county = row["county"].strip()
            state  = row["state"].strip()
            by_state.setdefault(abbr, []).append((county, state))
    return by_state


def build_related_block(county: str, state: str, state_abbr: str,
                        by_state: dict) -> str:
    candidates = [
        (c, s) for (c, s) in by_state.get(state_abbr, [])
        if c != county
    ]
    # Prefer a deterministic but varied selection: sort then pick evenly spaced
    candidates.sort(key=lambda x: x[0])
    if len(candidates) <= N_LINKS:
        picks = candidates
    else:
        step = len(candidates) // N_LINKS
        picks = candidates[::step][:N_LINKS]

    items = "\n".join(
        f'  <li><a href="/counties/{slug(c, s)}">'
        f"{c} County, {s} Inmate Lookup</a></li>"
        for c, s in picks
    )
    return f"""
{MARKER}
<div class="related-counties" style="margin:32px 0 8px;padding:20px;background:#f8f9fa;border-radius:8px;border:1px solid #e9ecef">
  <h2 style="margin-top:0;font-size:1.1em;color:#1d3557">Other {state} County Inmate Lookups</h2>
  <ul style="list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:6px">
{items}
  </ul>
</div>"""


def patch_file(path: Path, county: str, state: str, state_abbr: str,
               by_state: dict, dry_run: bool) -> bool:
    html = path.read_text(encoding="utf-8", errors="replace")
    if MARKER in html:
        return False  # already patched
    block = build_related_block(county, state, state_abbr, by_state)
    # Insert before </body>
    if "</body>" not in html:
        return False
    new_html = html.replace("</body>", block + "\n</body>", 1)
    if not dry_run:
        path.write_text(new_html, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--state", help="Only process this state abbreviation (e.g. TX)")
    args = parser.parse_args()

    by_state = load_counties()
    # Build a lookup: slug → (county, state, state_abbr)
    slug_map: dict[str, tuple[str, str, str]] = {}
    for abbr, entries in by_state.items():
        for county, state in entries:
            slug_map[slug(county, state)] = (county, state, abbr)

    files = sorted(COUNTY_DIR.glob("*.html"))
    updated = skipped = errors = 0

    for fpath in files:
        fname = fpath.name
        info  = slug_map.get(fname)
        if not info:
            # Try to parse county/state from filename
            # format: {county-words}-county-{state-words}-inmate-lookup.html
            m = re.match(r"^(.+)-county-(.+)-inmate-lookup\.html$", fname)
            if not m:
                errors += 1
                continue
            county_slug_part = m.group(1).replace("-", " ").title()
            state_slug_part  = m.group(2).replace("-", " ").title()
            # Find in by_state
            found = False
            for abbr, entries in by_state.items():
                for c, s in entries:
                    if c.lower() == county_slug_part.lower() and s.lower() == state_slug_part.lower():
                        info = (c, s, abbr)
                        found = True
                        break
                if found:
                    break
            if not info:
                errors += 1
                continue

        county, state, abbr = info

        if args.state and abbr != args.state.upper():
            continue

        try:
            did_update = patch_file(fpath, county, state, abbr, by_state, args.dry_run)
            if did_update:
                updated += 1
                if updated % 100 == 0:
                    print(f"  [{updated}] patched {fname}")
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR {fname}: {e}")
            errors += 1

    mode = "DRY RUN — " if args.dry_run else ""
    print(f"\n{mode}Done.")
    print(f"  Updated : {updated}")
    print(f"  Skipped : {skipped} (already patched)")
    print(f"  Errors  : {errors}")


if __name__ == "__main__":
    main()
