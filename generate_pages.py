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
    if not key:
        # Fallback: use template without AI
        return _template_fallback(county, state, state_abbr)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = f"""Write an informational HTML page body (no html/head/body tags) for people searching "{county} County {state} inmate lookup".

Requirements:
- H1: "{county} County {state} Inmate Lookup — Official Guide"  
- Intro paragraph (2 sentences, include keywords naturally)
- Section "How to Search {county} County Jail Records" with numbered steps
- Section "Official {county} County Resources" with a bulleted list (use placeholder href="#" for links)
- Section "Bail Information for {county} County {state}" (1 paragraph, general info)
- FAQ section with 3 realistic questions searchers ask
- Total: 400-500 words
- Clean semantic HTML only (h2, p, ul, ol, div)
- No lorem ipsum, be specific to {county} County {state}"""

        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠ AI failed ({e}), using template")
        return _template_fallback(county, state, state_abbr)


def _template_fallback(county: str, state: str, state_abbr: str) -> str:
    """Template-based fallback when AI is unavailable."""
    return f"""<h1>{county} County {state} Inmate Lookup — Official Guide</h1>
<p>Looking for {county} County {state} inmate information? This guide helps you find official jail records, 
court information, and inmate search tools for {county} County, {state}.</p>

<h2>How to Search {county} County Jail Records</h2>
<ol>
  <li>Visit the official {county} County Sheriff's Office website</li>
  <li>Navigate to the "Inmate Search" or "Jail Roster" section</li>
  <li>Enter the person's first and last name</li>
  <li>Review the results and note the booking number</li>
  <li>Contact the facility for visitation or bond information</li>
</ol>

<h2>Official {county} County Resources</h2>
<ul class="resource-list">
  <li><a href="#">{county} County Sheriff's Office — Inmate Search</a></li>
  <li><a href="#">{state_abbr} Department of Corrections</a></li>
  <li><a href="#">{county} County Court Records</a></li>
  <li><a href="#">Federal Bureau of Prisons Locator</a></li>
</ul>

<div class="cta-box">
  <strong>Need Help with Bail?</strong> Local bail bondsmen in {county} County can help secure release. 
  Standard bail bonds typically cost 10% of the total bail amount.
</div>

<h2>Frequently Asked Questions</h2>
<p><strong>How do I find out if someone is in {county} County jail?</strong><br>
Use the official {county} County Sheriff's Office inmate search tool online, or call the jail directly.</p>
<p><strong>How long does booking take in {county} County?</strong><br>
Booking typically takes 2-8 hours depending on the facility's current capacity.</p>
<p><strong>Can I visit an inmate at {county} County jail?</strong><br>
Yes, contact the {county} County Sheriff's Office for current visitation hours and requirements.</p>"""


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
    output_dir.mkdir(parents=True, exist_ok=True)
    built = []
    total = len(counties)

    for i, (county, state, state_abbr) in enumerate(counties, 1):
        filename = f"{county.lower().replace(' ', '-')}-county-{state.lower().replace(' ', '-')}-inmate-lookup.html"
        out_path = output_dir / filename

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

    build_index(built, output_dir)
    print(f"\n✅ Generated {len(built)} pages → {output_dir}")
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
