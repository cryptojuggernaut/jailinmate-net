"""
fix_state_pages.py
Regenerates all 50 state HTML pages with real county links pointing to /counties/*.html
Run from: C:\WebAutomation\projects\inmate-lookup-site\
"""
import os
import re
from pathlib import Path

DIST = Path(__file__).parent / "dist"
COUNTIES_DIR = DIST / "counties"
STATES_DIR = DIST / "states"

STATE_INFO = {
    "ak": ("Alaska",    "Alaska"),
    "al": ("Alabama",   "Alabama"),
    "ar": ("Arkansas",  "Arkansas"),
    "az": ("Arizona",   "Arizona"),
    "ca": ("California","California"),
    "co": ("Colorado",  "Colorado"),
    "ct": ("Connecticut","Connecticut"),
    "de": ("Delaware",  "Delaware"),
    "fl": ("Florida",   "Florida"),
    "ga": ("Georgia",   "Georgia"),
    "hi": ("Hawaii",    "Hawaii"),
    "ia": ("Iowa",      "Iowa"),
    "id": ("Idaho",     "Idaho"),
    "il": ("Illinois",  "Illinois"),
    "in": ("Indiana",   "Indiana"),
    "ks": ("Kansas",    "Kansas"),
    "ky": ("Kentucky",  "Kentucky"),
    "la": ("Louisiana", "Louisiana"),
    "ma": ("Massachusetts","Massachusetts"),
    "md": ("Maryland",  "Maryland"),
    "me": ("Maine",     "Maine"),
    "mi": ("Michigan",  "Michigan"),
    "mn": ("Minnesota", "Minnesota"),
    "mo": ("Missouri",  "Missouri"),
    "ms": ("Mississippi","Mississippi"),
    "mt": ("Montana",   "Montana"),
    "nc": ("North Carolina","North Carolina"),
    "nd": ("North Dakota","North Dakota"),
    "ne": ("Nebraska",  "Nebraska"),
    "nh": ("New Hampshire","New Hampshire"),
    "nj": ("New Jersey","New Jersey"),
    "nm": ("New Mexico","New Mexico"),
    "nv": ("Nevada",    "Nevada"),
    "ny": ("New York",  "New York"),
    "oh": ("Ohio",      "Ohio"),
    "ok": ("Oklahoma",  "Oklahoma"),
    "or": ("Oregon",    "Oregon"),
    "pa": ("Pennsylvania","Pennsylvania"),
    "ri": ("Rhode Island","Rhode Island"),
    "sc": ("South Carolina","South Carolina"),
    "sd": ("South Dakota","South Dakota"),
    "tn": ("Tennessee", "Tennessee"),
    "tx": ("Texas",     "Texas"),
    "ut": ("Utah",      "Utah"),
    "va": ("Virginia",  "Virginia"),
    "vt": ("Vermont",   "Vermont"),
    "wa": ("Washington","Washington"),
    "wi": ("Wisconsin", "Wisconsin"),
    "wv": ("West Virginia","West Virginia"),
    "wy": ("Wyoming",   "Wyoming"),
}

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{state_name} Jail Inmate Lookup — All {count} Counties</title>
<meta name="description" content="Find inmate records for all {count} counties in {state_name}. Official links to sheriff offices, jail rosters, and court records.">
<meta name="google-site-verification" content="WzK04VtHcUWuo5mpnptZdpeX7_jm08JZYIpkF-QXgs4">
<link rel="canonical" href="https://jailinmate.net/states/{abbr}.html">
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--border:#2a2d3a;--text:#e8eaf0;--muted:#8b90a0;--accent:#4f7cff;--green:#22c55e;--red:#ef4444}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6}}
a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}
.container{{max-width:1100px;margin:0 auto;padding:0 20px}}
nav{{background:#111320;border-bottom:1px solid var(--border);padding:14px 0;position:sticky;top:0;z-index:100}}
.nav-inner{{display:flex;align-items:center;justify-content:space-between}}
.logo{{font-size:20px;font-weight:800;color:#fff;letter-spacing:-0.5px}}
.logo span{{color:var(--accent)}}
.nav-links{{display:flex;gap:24px;font-size:14px}}
.nav-links a{{color:var(--muted)}}
.section{{padding:60px 0}}
.section-title{{font-size:24px;font-weight:700;margin-bottom:24px}}
.breadcrumb{{font-size:13px;color:var(--muted);padding:16px 0}}
.breadcrumb a{{color:var(--muted)}}
.content-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:28px;margin-bottom:20px}}
.county-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}
.county-link{{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:12px 15px;font-size:14px;transition:border-color .15s;display:block;color:var(--accent)}}
.county-link:hover{{border-color:var(--accent);text-decoration:none}}
footer{{background:#0a0c14;border-top:1px solid var(--border);padding:40px 0;color:var(--muted);font-size:13px;text-align:center}}
footer a{{color:var(--muted)}}
.disclaimer{{background:#1a1d27;border:1px solid var(--border);border-radius:8px;padding:16px;font-size:12px;color:var(--muted);margin-top:30px}}
h1,h2{{letter-spacing:-0.5px}}
</style>
<meta name="google-adsense-account" content="ca-pub-1410717606678785">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1410717606678785" crossorigin="anonymous"></script>
</head>
<body>
<nav>
<div class="container nav-inner">
  <a href="/" class="logo">Jail<span>Inmate</span>.net</a>
  <div class="nav-links">
    <a href="/states.html">All States</a>
    <a href="/about.html">About</a>
    <a href="/privacy.html">Privacy</a>
  </div>
</div>
</nav>

<div class="section">
<div class="container">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/states.html">States</a> › {state_name}</div>
  <h1 class="section-title">{state_name} Jail Inmate Lookup</h1>
  <p style="color:var(--muted);margin-bottom:24px">Select a county to find official inmate search resources for {state_name}.</p>
  <div class="content-card">
    <p style="margin-bottom:16px;font-size:14px;color:var(--muted)">{count} counties in {state_name}</p>
    <div class="county-grid">{county_links}</div>
  </div>
  <div class="disclaimer">
    <strong>Disclaimer:</strong> This page links to official government resources only.
    We are not affiliated with any government agency or law enforcement.
  </div>
</div>
</div>
<footer>
<div class="container">
  <p style="margin-bottom:12px"><a href="/" style="font-weight:700;color:#fff">jailinmate.net</a></p>
  <p><a href="/states.html">All States</a> &nbsp;·&nbsp; <a href="/about.html">About</a> &nbsp;·&nbsp; <a href="/privacy.html">Privacy Policy</a> &nbsp;·&nbsp; <a href="/contact.html">Contact</a></p>
  <p style="margin-top:16px">© 2026 jailinmate.net — Informational resource linking to official government sources.</p>
  <p style="margin-top:8px">We do not store, sell, or distribute personal information. All links go to official government websites.</p>
</div>
</footer>
</body>
</html>
"""

def get_counties_for_state(state_abbr: str, state_in_filename: str) -> list[tuple[str, str]]:
    """Return list of (display_name, filename) for a state's counties."""
    pattern = f"-{state_in_filename.lower().replace(' ', '-')}-inmate-lookup.html"
    counties = []
    for f in sorted(COUNTIES_DIR.glob(f"*{pattern}")):
        # Extract county name from filename: "fairfield-county-connecticut-inmate-lookup.html"
        stem = f.stem  # e.g. "fairfield-county-connecticut-inmate-lookup"
        # Remove the state suffix and "-inmate-lookup"
        state_slug = state_in_filename.lower().replace(' ', '-')
        county_part = stem.replace(f"-{state_slug}-inmate-lookup", "")
        display = county_part.replace("-", " ").title()
        counties.append((display, f.name))
    return counties


def build_state_page(abbr: str):
    state_key, state_name = STATE_INFO[abbr]
    counties = get_counties_for_state(abbr, state_name)

    if not counties:
        print(f"  WARNING: No counties found for {state_name} ({abbr}), skipping.")
        return False

    links_html = "\n".join(
        f'<a class="county-link" href="/counties/{fname}">📋 {display}</a>'
        for display, fname in counties
    )

    html = HTML_TEMPLATE.format(
        state_name=state_name,
        abbr=abbr,
        count=len(counties),
        county_links=links_html,
    )

    out_path = STATES_DIR / f"{abbr}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  OK {abbr}.html - {len(counties)} counties")
    return True


def main():
    print(f"Fixing state pages in: {STATES_DIR}")
    print(f"Reading counties from:  {COUNTIES_DIR}\n")

    ok = 0
    skipped = 0
    for abbr in sorted(STATE_INFO.keys()):
        if build_state_page(abbr):
            ok += 1
        else:
            skipped += 1

    print(f"\nDone. {ok} state pages fixed, {skipped} skipped (no counties found).")


if __name__ == "__main__":
    main()
