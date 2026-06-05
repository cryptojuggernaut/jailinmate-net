"""
Inmate Lookup Site — County Page Generator
projects/inmate-lookup-site/generate_pages.py

Generates 3,000 static HTML pages (one per US county) using Claude.
Deploys to: C:\WebAutomation\projects\inmate-lookup-site\dist\

Usage:
  python generate_pages.py              # Generate first 10 (test)
  python generate_pages.py --all        # Generate all 3,000
  python generate_pages.py --state TX   # Generate one state only
"""
import os, sys, json, time, argparse
from pathlib import Path

# Top 50 US counties by population for fast first batch
SAMPLE_COUNTIES = [
    ("Los Angeles", "California", "CA"),
    ("Cook", "Illinois", "IL"),
    ("Harris", "Texas", "TX"),
    ("Maricopa", "Arizona", "AZ"),
    ("San Diego", "California", "CA"),
    ("Dallas", "Texas", "TX"),
    ("Orange", "California", "CA"),
    ("Kings", "New York", "NY"),
    ("Miami-Dade", "Florida", "FL"),
    ("Riverside", "California", "CA"),
    ("Clark", "Nevada", "NV"),
    ("Tarrant", "Texas", "TX"),
    ("San Bernardino", "California", "CA"),
    ("King", "Washington", "WA"),
    ("Bexar", "Texas", "TX"),
    ("Broward", "Florida", "FL"),
    ("Wayne", "Michigan", "MI"),
    ("Alameda", "California", "CA"),
    ("Middlesex", "Massachusetts", "MA"),
    ("Philadelphia", "Pennsylvania", "PA"),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{county} County {state} Inmate Lookup — Official Guide</title>
<meta name="description" content="How to search {county} County {state} inmate records, jail roster, and court information. Official sources and step-by-step guide.">
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
  h1 {{ color: #1a1a2e; border-bottom: 3px solid #e63946; padding-bottom: 10px; }}
  h2 {{ color: #457b9d; margin-top: 30px; }}
  .cta-box {{ background: #f1faee; border: 1px solid #a8dadc; padding: 16px; border-radius: 8px; margin: 20px 0; }}
  .resource-list {{ list-style: none; padding: 0; }}
  .resource-list li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
  .resource-list a {{ color: #457b9d; }}
  footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.85em; }}
  nav {{ background: #1a1a2e; padding: 10px 20px; margin: -20px -20px 20px; }}
  nav a {{ color: white; text-decoration: none; font-weight: bold; }}
</style>
</head>
<body>
<nav><a href="/">🏛️ jailinmate.net</a></nav>
{body}
<footer>
  <p>This is an informational guide page. We link to official government sources only. We are not affiliated with any government agency.</p>
  <p><a href="/">Home</a> | <a href="/states.html">All States</a></p>
</footer>
</body>
</html>"""


def generate_page_content(county: str, state: str, state_abbr: str) -> str:
    """Generate the body content for a county page using Claude."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    real_links = _get_real_links(county, state, state_abbr)

    if not key:
        return _template_fallback(county, state, state_abbr, real_links)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = f"""Write an informational HTML body (no html/head/body/doctype tags, NO markdown code fences) for people searching "{county} County {state} inmate lookup".

Requirements:
- H1: "{county} County {state} Inmate Lookup"
- Intro paragraph specific to {county} County (2-3 sentences)
- Section "How to Search {county} County Jail Records" with numbered steps
- Section "Official {county} County Resources" with working links using these EXACT hrefs:
{real_links['links_html']}
- Section "Bail Information for {county} County {state}" (1 paragraph, mention 10% bondsman fee)
- FAQ section with 3 realistic questions and answers
- Total: 400-500 words
- IMPORTANT: Use only clean semantic HTML (h2, p, ul, ol, div). NO href="#". NO markdown. NO code blocks."""

        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        content = resp.content[0].text.strip()
        # Strip any markdown code fences Claude accidentally adds
        content = content.removeprefix("```html").removeprefix("```").removesuffix("```").strip()
        return content
    except Exception as e:
        print(f"  AI failed ({e}), using template")
        return _template_fallback(county, state, state_abbr, real_links)


def _get_real_links(county: str, state: str, state_abbr: str) -> dict:
    """Return real working URLs for a given county."""
    county_slug = county.lower().replace(" ", "-")
    state_slug = state.lower().replace(" ", "-")
    state_lower = state_abbr.lower()

    # Federal Bureau of Prisons locator — always works
    fbop = "https://www.bop.gov/inmateloc/"

    # State DOC URLs — real links for all 50 states
    state_doc_urls = {
        "AL": "https://www.doc.state.al.us/", "AK": "https://doc.alaska.gov/",
        "AZ": "https://corrections.az.gov/", "AR": "https://doc.arkansas.gov/",
        "CA": "https://www.cdcr.ca.gov/", "CO": "https://cdoc.colorado.gov/",
        "CT": "https://portal.ct.gov/DOC", "DE": "https://doc.delaware.gov/",
        "FL": "https://www.dc.state.fl.us/", "GA": "https://gdc.georgia.gov/",
        "HI": "https://dps.hawaii.gov/", "ID": "https://www.idoc.idaho.gov/",
        "IL": "https://idoc.illinois.gov/", "IN": "https://www.in.gov/idoc/",
        "IA": "https://doc.iowa.gov/", "KS": "https://www.doc.ks.gov/",
        "KY": "https://corrections.ky.gov/", "LA": "https://doc.louisiana.gov/",
        "ME": "https://www.maine.gov/corrections/", "MD": "https://dpscs.maryland.gov/",
        "MA": "https://www.mass.gov/orgs/department-of-correction",
        "MI": "https://www.michigan.gov/mdoc", "MN": "https://mn.gov/doc/",
        "MS": "https://www.mdoc.ms.gov/", "MO": "https://doc.mo.gov/",
        "MT": "https://cor.mt.gov/", "NE": "https://corrections.nebraska.gov/",
        "NV": "https://doc.nv.gov/", "NH": "https://www.nh.gov/nhdoc/",
        "NJ": "https://www.state.nj.us/corrections/", "NM": "https://cd.nm.gov/",
        "NY": "https://doccs.ny.gov/", "NC": "https://www.dac.nc.gov/",
        "ND": "https://www.docr.nd.gov/", "OH": "https://drc.ohio.gov/",
        "OK": "https://oklahoma.gov/doc.html", "OR": "https://www.oregon.gov/doc",
        "PA": "https://www.cor.pa.gov/", "RI": "https://doc.ri.gov/",
        "SC": "https://www.doc.sc.gov/", "SD": "https://doc.sd.gov/",
        "TN": "https://www.tn.gov/correction.html", "TX": "https://www.tdcj.texas.gov/",
        "UT": "https://corrections.utah.gov/", "VT": "https://doc.vermont.gov/",
        "VA": "https://vadoc.virginia.gov/", "WA": "https://doc.wa.gov/",
        "WV": "https://dcr.wv.gov/", "WI": "https://doc.wi.gov/",
        "WY": "https://corrections.wyo.gov/", "DC": "https://doc.dc.gov/",
    }

    doc_url = state_doc_urls.get(state_abbr, f"https://www.google.com/search?q={state_slug}+department+of+corrections")

    # Google searches for county-specific resources (always valid, always relevant)
    sheriff_search = f"https://www.google.com/search?q={county_slug}+county+{state_lower}+sheriff+inmate+search"
    court_search = f"https://www.google.com/search?q={county_slug}+county+{state_lower}+court+records"
    bond_search = f"https://www.google.com/search?q={county_slug}+county+{state_lower}+bail+bonds"

    links_html = f"""  <li><a href="{sheriff_search}">{county} County Sheriff's Office — Inmate Search</a></li>
  <li><a href="{doc_url}">{state} Department of Corrections Inmate Locator</a></li>
  <li><a href="{court_search}">{county} County Court Records</a></li>
  <li><a href="{fbop}">Federal Bureau of Prisons Inmate Locator</a></li>
  <li><a href="{bond_search}">{county} County Bail Bond Information</a></li>"""

    return {
        "sheriff_search": sheriff_search,
        "doc_url": doc_url,
        "fbop": fbop,
        "links_html": links_html,
    }



def _template_fallback(county: str, state: str, state_abbr: str, real_links: dict = None) -> str:
    """Template-based fallback when AI is unavailable."""
    if real_links is None:
        real_links = _get_real_links(county, state, state_abbr)
    return f"""<h1>{county} County {state} Inmate Lookup — Official Guide</h1>
<p>Looking for someone in {county} County, {state}? This guide explains how to search official {county} County jail records,
view current inmates, and access court information for {county} County, {state}.</p>

<h2>How to Search {county} County Jail Records</h2>
<ol>
  <li>Click the <a href="{real_links['sheriff_search']}">{county} County Sheriff's Office inmate search</a> link below</li>
  <li>Enter the person's first and last name in the search fields</li>
  <li>Review results — records typically show booking date, charges, and bond amount</li>
  <li>Note the booking number for phone inquiries with the facility</li>
  <li>Contact the jail directly if the person doesn't appear online yet — processing takes 2-8 hours</li>
</ol>

<h2>Official {county} County Resources</h2>
<ul class="resource-list">
{real_links['links_html']}
</ul>

<div class="cta-box">
  <strong>Need Help with Bail?</strong> Licensed bail bondsmen in {county} County can help secure release.
  Standard bail bonds typically cost 10% of the total bail amount set by the court.
</div>

<h2>Frequently Asked Questions</h2>
<p><strong>How do I find out if someone is in {county} County jail?</strong><br>
Use the <a href="{real_links['sheriff_search']}">official {county} County Sheriff's Office inmate search</a>, or call the jail directly. Records update every 2-8 hours after booking.</p>

<p><strong>How long does booking take in {county} County?</strong><br>
Booking typically takes 2-8 hours depending on the facility's current capacity. During weekends and holidays it may take longer before the record appears online.</p>

<p><strong>Can I visit an inmate at {county} County jail?</strong><br>
Yes. Contact the {county} County Sheriff's Office for current visitation hours, approved ID requirements, and dress code rules. Some facilities also offer video visitation.</p>

<p><strong>What if the person is in a state or federal facility?</strong><br>
Use the <a href="{real_links['doc_url']}">{state} Department of Corrections inmate locator</a> for state prisons, or the
<a href="{real_links['fbop']}">Federal Bureau of Prisons locator</a> for federal inmates.</p>"""



def build_index(counties_built: list, output_dir: Path):
    """Build a simple index page."""
    links = "\n".join(
        f'<li><a href="{c.lower().replace(" ", "-")}-county-{s.lower().replace(" ", "-")}-inmate-lookup.html">'
        f'{c} County, {s}</a></li>'
        for c, s, _ in counties_built
    )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>US County Inmate Lookup — Find Anyone in Any US County Jail</title>
<meta name="description" content="Search inmate records for any US county. Official guides for all 3,000+ counties.">
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:20px}}
h1{{color:#1a1a2e}}ul{{columns:2;list-style:none;padding:0}}li{{padding:4px 0}}a{{color:#457b9d}}</style>
</head><body>
<h1>🏛️ US County Inmate Lookup</h1>
<p>Find official inmate search resources for all US counties. Select your county below.</p>
<ul>{links}</ul>
</body></html>"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def run(counties: list, output_dir: Path, delay: float = 0.5):
    """Generate pages for the given county list."""
    # Write county pages to a subdirectory so they don't clobber build_site.py output
    county_dir = output_dir / "counties"
    county_dir.mkdir(parents=True, exist_ok=True)
    built = []
    total = len(counties)

    for i, (county, state, state_abbr) in enumerate(counties, 1):
        filename = f"{county.lower().replace(' ', '-')}-county-{state.lower().replace(' ', '-')}-inmate-lookup.html"
        out_path = county_dir / filename

        if out_path.exists():
            print(f"  [{i}/{total}] SKIP {county} County, {state} (exists)")
            built.append((county, state, state_abbr))
            continue

        print(f"  [{i}/{total}] Generating {county} County, {state}...")
        body = generate_page_content(county, state, state_abbr)
        html = HTML_TEMPLATE.format(county=county, state=state, state_abbr=state_abbr, body=body)
        out_path.write_text(html, encoding="utf-8")
        built.append((county, state, state_abbr))
        time.sleep(delay)  # Rate limit

    # Do NOT call build_index() — index.html is owned by build_site.py
    print(f"\nDone. Generated {len(built)} county pages -> {county_dir}")
    return built


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Generate all counties (requires CSV)")
    parser.add_argument("--state", help="Filter by state abbreviation (e.g. TX)")
    parser.add_argument("--count", type=int, default=10, help="Number of counties to generate")
    args = parser.parse_args()

    out = Path(r"C:\WebAutomation\projects\inmate-lookup-site\dist")

    if args.all:
        # Load from CSV if available
        csv_path = Path(r"C:\WebAutomation\projects\inmate-lookup-site\counties.csv")
        if csv_path.exists():
            import csv
            with open(csv_path) as f:
                all_counties = [(r["county"], r["state"], r["state_abbr"]) for r in csv.DictReader(f)]
        else:
            print("No counties.csv found — using sample list")
            all_counties = SAMPLE_COUNTIES
        counties = [c for c in all_counties if not args.state or c[2] == args.state]
    else:
        counties = SAMPLE_COUNTIES[:args.count]
        if args.state:
            counties = [c for c in SAMPLE_COUNTIES if c[2] == args.state]

    run(counties, out)
