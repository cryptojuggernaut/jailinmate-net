"""
Inmate Lookup Site — County Page Generator
projects/inmate-lookup-site/generate_pages.py

Generates 3,000 static HTML pages (one per US county) using Claude.
Deploys to: C:/WebAutomation/projects/inmate-lookup-site/dist/

Usage:
  python generate_pages.py              # Generate first 10 (test)
  python generate_pages.py --all        # Generate all 3,000
  python generate_pages.py --state TX   # Generate one state only

Keyword integration:
  Run keyword_agent.py first to populate keyword_data/keyword_map.json.
  generate_pages.py reads that map and uses the researched keyword as the
  primary keyword for title, H1, and Claude prompt.
"""
import os, sys, json, time, argparse
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# Fix SSL certificate verification on Windows (Python 3.14 doesn't use system cert store)
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# ── Site Launch Wizard: load approved blueprint from SCE DB ─────────────────
def _load_blueprint_system_prompt(project: str = "inmate-lookup-site") -> str:
    """
    Read the approved blueprint from SCE's site_plans table and extract
    the content rules for injection as Claude's system prompt.
    Falls back to '' if the DB is unavailable or no approved plan exists.
    Phase 5 of the Site Launch Wizard.
    """
    try:
        import sqlite3
        import re
        db = Path(__file__).parents[2] / "sce" / "db" / "sce.db"
        if not db.exists():
            return ""
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT blueprint_md FROM site_plans WHERE project=? AND status='approved' "
            "ORDER BY version DESC LIMIT 1",
            (project,)
        )
        row = cur.fetchone()
        conn.close()
        if not row or not row["blueprint_md"]:
            return ""
        bp = row["blueprint_md"]
        # Extract the content rules sections: Page Template + Quality Rules
        sections = []
        for header in [
            "## Page Template",
            "## Quality Rules",
            "## Schema Markup",
            "## Validation Gate",
        ]:
            m = re.search(rf"{re.escape(header)}.*?(?=\n## |\Z)", bp, re.S)
            if m:
                sections.append(m.group(0).strip())
        if not sections:
            return ""
        system = (
            "You are a specialist HTML writer generating county inmate lookup pages. "
            "Follow these approved blueprint rules exactly:\n\n"
            + "\n\n".join(sections)
        )
        return system
    except Exception as e:
        print(f"[blueprint] Could not load from SCE DB: {e}")
        return ""


_BLUEPRINT_SYSTEM = _load_blueprint_system_prompt()
if _BLUEPRINT_SYSTEM:
    print(f"[blueprint] Loaded approved blueprint from SCE ({len(_BLUEPRINT_SYSTEM)} chars) — wizard rules active")
else:
    print("[blueprint] No approved blueprint found — using hardcoded rules")


# Load keyword map produced by keyword_agent.py (optional — degrades gracefully)
_KEYWORD_MAP_PATH = Path(__file__).parent / "keyword_data" / "keyword_map.json"
_KEYWORD_MAP: dict = {}
if _KEYWORD_MAP_PATH.exists():
    try:
        _KEYWORD_MAP = json.loads(_KEYWORD_MAP_PATH.read_text(encoding="utf-8"))
        print(f"[keywords] Loaded {len(_KEYWORD_MAP)} researched keywords")
    except Exception:
        pass

# Load real county data (sheriff URLs, addresses, phones) — replaces Google Search fallbacks
_COUNTY_DATA_PATH = Path(__file__).parent / "county_data.json"
_COUNTY_DATA: dict = {}
if _COUNTY_DATA_PATH.exists():
    try:
        _COUNTY_DATA = json.loads(_COUNTY_DATA_PATH.read_text(encoding="utf-8"))
        print(f"[county_data] Loaded real data for {len(_COUNTY_DATA)} counties")
    except Exception as e:
        print(f"[county_data] Failed to load: {e}")


def get_primary_keyword(county: str, state: str, state_abbr: str) -> str:
    """Return the researched primary keyword, or a sensible default."""
    key = f"{county}|{state}"
    return _KEYWORD_MAP.get(key, f"{county} County {state} Inmate Lookup")


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
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://jailinmate.net/{slug}">

<!-- Open Graph (social sharing) -->
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://jailinmate.net/{slug}">
<meta property="og:site_name" content="jailinmate.net">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
{schema_json}
</script>

<!-- AdSense -->
<meta name="google-adsense-account" content="ca-pub-1410717606678785">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1410717606678785" crossorigin="anonymous"></script>

<style>
  *{{box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:860px;margin:0 auto;padding:0 20px 40px;color:#1a1a2e;line-height:1.7;font-size:16px}}
  h1{{color:#1a1a2e;border-bottom:3px solid #e63946;padding-bottom:12px;font-size:1.9em;margin-top:28px}}
  h2{{color:#1d3557;margin-top:36px;font-size:1.25em;border-left:4px solid #457b9d;padding-left:10px}}
  h3{{color:#457b9d;margin-top:20px;font-size:1.05em}}
  a{{color:#457b9d}}a:hover{{color:#1d3557}}
  ol,ul{{padding-left:22px}}
  li{{margin-bottom:6px}}
  .cta-box{{background:#f1faee;border:1px solid #a8dadc;padding:18px 20px;border-radius:8px;margin:24px 0}}
  .resource-list{{list-style:none;padding:0}}
  .resource-list li{{padding:9px 0;border-bottom:1px solid #eee}}
  .resource-list a{{color:#457b9d;font-weight:500}}
  .county-info-card{{background:#f8f9ff;border:1px solid #a8dadc;border-left:5px solid #457b9d;padding:16px 20px;border-radius:8px;margin:20px 0 28px}}
  .county-info-card h2{{margin-top:0;font-size:1.1em;color:#1d3557;border:none;padding:0}}
  .county-info-card ul{{margin:8px 0 0;padding-left:18px}}
  .county-info-card li{{margin-bottom:5px;font-size:0.95em}}
  .disclaimer{{background:#fff8e7;border:1px solid #f4d03f;padding:14px;border-radius:6px;font-size:0.88em;color:#7d6608;margin-top:32px}}
  footer{{margin-top:40px;padding-top:20px;border-top:1px solid #eee;color:#666;font-size:0.85em}}
  footer a{{color:#666}}
  nav{{background:#1a1a2e;padding:12px 20px;margin:0 -20px 24px;display:flex;gap:20px}}
  nav a{{color:white;text-decoration:none;font-weight:600;font-size:14px}}
  .breadcrumb{{font-size:13px;color:#888;margin-bottom:8px}}
  .breadcrumb a{{color:#888}}
  @media(max-width:600px){{h1{{font-size:1.4em}}h2{{font-size:1.1em}}}}
</style>
</head>
<body>
<nav>
  <a href="/">🏛️ jailinmate.net</a>
  <a href="/states.html">All States</a>
  <a href="/about.html">About</a>
</nav>
<div class="breadcrumb"><a href="/">Home</a> › <a href="/states/{state_abbr_lower}.html">{state}</a> › {county} County</div>
{body}
<div class="disclaimer">
  <strong>Disclaimer:</strong> jailinmate.net is an informational resource that links to official government websites.
  We are not affiliated with any law enforcement agency, court, or government body.
  All inmate search links go directly to official sheriff offices or government databases.
  We do not store, sell, or distribute personal information.
</div>
<footer>
  <p><a href="/">Home</a> &nbsp;·&nbsp; <a href="/states.html">All States</a> &nbsp;·&nbsp; <a href="/states/{state_abbr_lower}.html">{state} Counties</a> &nbsp;·&nbsp; <a href="/about.html">About</a> &nbsp;·&nbsp; <a href="/privacy.html">Privacy</a> &nbsp;·&nbsp; <a href="/terms.html">Terms</a></p>
  <p style="margin-top:8px">© 2025 jailinmate.net — Links to official government sources only.</p>
</footer>
</body>
</html>"""


def _validate_body(content: str, county: str, real_links: dict) -> list[str]:
    """
    Return a list of quality issues found in AI-generated body HTML.
    Empty list = page is good to write. Non-empty = fall back to template.

    Rules enforced here match the site blueprint v2 quality standards.
    """
    issues = []
    # Must contain actual HTML tags
    if "<h1" not in content and "<p" not in content:
        issues.append("no HTML tags found (likely markdown output)")
    # Must not contain markdown fences
    if "```" in content:
        issues.append("contains markdown code fences")
    # Must not contain dead links
    if 'href="#"' in content:
        issues.append("contains dead href='#' links")
    # Must have an H1
    if "<h1" not in content.lower():
        issues.append("missing <h1>")
    # Must have at least 4 of the 7 required H2 sections (partial match is OK)
    required_h2s = ["How to Search", "Official", "Bail Bond", "Visitation", "What to Expect", "How to Contact", "Frequently Asked"]
    found = sum(1 for h in required_h2s if h.lower() in content.lower())
    if found < 6:  # require at least 6/7 — fall back to template if 2+ sections missing
        issues.append(f"only {found}/7 required H2 sections found")
    # Must contain at least one real external link (http)
    if "http" not in content:
        issues.append("no external links found")
    # Must not be too short (template fallback is ~1800 chars; AI should exceed that)
    if len(content) < 1200:
        issues.append(f"content too short ({len(content)} chars)")
    if "google.com/search" in content.lower() or "google.com/url" in content.lower():
        issues.append("contains google search URL (forbidden)")
    # Must not start with a code fence leftover
    if content.lstrip().startswith("html"):
        issues.append("starts with 'html' (markdown fence artifact)")
    return issues


def generate_page_content(county: str, state: str, state_abbr: str,
                          primary_keyword: str = None) -> str:
    """Generate the body content for a county page using Claude."""
    if primary_keyword is None:
        primary_keyword = get_primary_keyword(county, state, state_abbr)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    real_links = _get_real_links(county, state, state_abbr)

    if not key or os.environ.get("SCE_INMATE_TEMPLATE_ONLY") == "1":
        return _template_fallback(county, state, state_abbr, real_links, primary_keyword)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = f"""Write an informational HTML body (no html/head/body/doctype tags, NO markdown code fences) for people searching "{primary_keyword}".

REQUIRED STRUCTURE — use exactly these 7 H2 headings in this order:
1. <h2>How to Search {county} County Jail Records</h2> — numbered steps (ol)
2. <h2>Official {county} County Resources</h2> — use EXACTLY these links:
{real_links['links_html']}
3. <h2>Bail Bond Information for {county} County</h2> — 2 paragraphs, mention 10% bondsman fee, arraignment timeline
4. <h2>Visitation Rules at {county} County Jail</h2> — ul with ID, hours, dress code, video visits, children policy
5. <h2>What to Expect After Arrest in {county} County</h2> — numbered steps: booking, medical, classification, arraignment, transfer
6. <h2>How to Contact {county} County Jail</h2> — paragraph + ul with the 3 official links above
7. <h2>Frequently Asked Questions — {county} County Inmate Lookup</h2> — exactly 5 <h3> questions with <p> answers:
   - How do I find out if someone is in {county} County jail?
   - How long does booking take in {county} County?
   - Can I visit an inmate at {county} County jail?
   - What if the person is not in the county jail system?
   - How do I send money to an inmate in {county} County?

RULES:
- H1: "{primary_keyword}"
- Intro paragraph: 2-3 sentences, naturally include "{primary_keyword.lower()}"
- Total: 800-900 words (each section needs enough detail to be useful)
- Use only semantic HTML (h1, h2, h3, p, ul, ol, li, strong, a). NO href="#". NO markdown. NO code blocks.
- Link text must be descriptive (no "click here")
- NEVER use google.com/search, bing.com/search, or any web-search URL. Only the resource links provided above (or plain text if no URL).
- Do not label a link "official" unless it is one of the provided government/facility URLs."""

        api_kwargs = dict(
            model="claude-haiku-4-5",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        if _BLUEPRINT_SYSTEM:
            api_kwargs["system"] = _BLUEPRINT_SYSTEM
        resp = client.messages.create(**api_kwargs)
        content = resp.content[0].text.strip()
        # Strip any markdown code fences Claude accidentally adds
        for fence in ("```html", "```"):
            if content.startswith(fence):
                content = content[len(fence):]
            if content.endswith("```"):
                content = content[:-3]
        content = content.strip()
        # Validate before returning — fall back to template if output is bad
        issues = _validate_body(content, county, real_links)
        if issues:
            print(f"  AI output failed validation ({'; '.join(issues)}) — using template")
            return _template_fallback(county, state, state_abbr, real_links, primary_keyword)
        return content
    except Exception as e:
        print(f"  AI failed ({e}), using template")
        return _template_fallback(county, state, state_abbr, real_links)


def _get_real_links(county: str, state: str, state_abbr: str) -> dict:
    """Return official resource links for a county.

    NEVER emits google.com/search (or any Google search URL) as an "official" link.
    Missing roster URLs → honest text guidance + state DOC + BOP only.
    """
    county_slug = county.lower().replace(" ", "-")
    state_slug = state.lower().replace(" ", "-")
    state_lower = state_abbr.lower()

    fbop = "https://www.bop.gov/inmateloc/"

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
    doc_url = state_doc_urls.get(state_abbr, "")

    def _clean_url(u: str) -> str:
        u = (u or "").strip()
        if not u:
            return ""
        low = u.lower()
        if "google.com/search" in low or "google.com/url" in low or "bing.com/search" in low:
            return ""
        if not (low.startswith("http://") or low.startswith("https://")):
            return ""
        return u

    data_key = f"{county}|{state}"
    cd = _COUNTY_DATA.get(data_key) or {}
    inmate_search = _clean_url(cd.get("inmate_search_url", ""))
    sheriff_site = _clean_url(cd.get("sheriff_url", ""))
    court_url = _clean_url(cd.get("court_url", ""))
    jail_name = cd.get("jail_name") or f"{county} County Jail"
    jail_address = cd.get("jail_address") or ""
    jail_phone = cd.get("jail_phone") or ""
    sheriff_name = cd.get("sheriff_name") or f"{county} County Sheriff's Office"
    has_real = bool(inmate_search or sheriff_site or jail_address or jail_phone)

    items = []
    if inmate_search:
        items.append(
            f'  <li><a href="{inmate_search}">{county} County official inmate roster / search</a></li>'
        )
    if sheriff_site:
        items.append(f'  <li><a href="{sheriff_site}">{sheriff_name}</a></li>')
    if doc_url:
        items.append(
            f'  <li><a href="{doc_url}">{state} Department of Corrections</a></li>'
        )
    items.append(f'  <li><a href="{fbop}">Federal Bureau of Prisons inmate locator</a></li>')
    if court_url:
        items.append(f'  <li><a href="{court_url}">{county} County court records</a></li>')
    if not inmate_search:
        items.append(
            f"  <li><strong>County roster online:</strong> No verified public inmate-search URL "
            f"on file for {county} County. Call the {sheriff_name}"
            + (f" at {jail_phone}" if jail_phone else "")
            + " or check the state DOC link above. "
            "We do not link to third-party web search results as “official” sources.</li>"
        )

    links_html = "\n".join(items)

    # Primary CTA: real roster, else sheriff site, else DOC, else empty (template uses text)
    primary = inmate_search or sheriff_site or doc_url or ""

    return {
        "sheriff_search": primary,
        "inmate_search": inmate_search,
        "sheriff_site": sheriff_site,
        "doc_url": doc_url,
        "fbop": fbop,
        "court_search": court_url,
        "bond_search": "",
        "links_html": links_html,
        "has_real_data": has_real,
        "has_roster_url": bool(inmate_search),
        "jail_name": jail_name,
        "jail_address": jail_address,
        "jail_phone": jail_phone,
        "sheriff_name": sheriff_name,
        "county_slug": county_slug,
        "state_slug": state_slug,
        "state_lower": state_lower,
    }


def _safe_href(url: str, label: str) -> str:
    """Anchor if URL present; plain text label otherwise. Never Google."""
    url = (url or "").strip()
    if url and "google.com/search" not in url.lower():
        return f'<a href="{url}">{label}</a>'
    return f"<strong>{label}</strong>"


def _county_info_card(county: str, state: str, real_links: dict) -> str:
    """County-specific info card with real jail data when available."""
    addr = real_links.get("jail_address", "")
    phone = real_links.get("jail_phone", "")
    jail_name = real_links.get("jail_name", f"{county} County Jail")
    inmate_url = real_links.get("inmate_search") or ""
    sheriff_site = real_links.get("sheriff_site") or ""
    if not (addr or phone or inmate_url or sheriff_site or real_links.get("has_real_data")):
        return ""
    card_lines = [
        f'<div class="county-info-card">',
        f"<h2>{jail_name} — Quick Facts</h2>",
        f"<ul>",
    ]
    if addr:
        card_lines.append(f"<li><strong>Address:</strong> {addr}</li>")
    if phone:
        card_lines.append(f"<li><strong>Phone:</strong> {phone}</li>")
    if inmate_url:
        card_lines.append(
            f'<li><strong>Official inmate search:</strong> <a href="{inmate_url}">{county} County roster</a></li>'
        )
    elif sheriff_site:
        card_lines.append(
            f'<li><strong>Sheriff office:</strong> <a href="{sheriff_site}">{real_links.get("sheriff_name")}</a></li>'
        )
    card_lines += [
        "<li><strong>Booking records:</strong> Often lag 2–8 hours after arrest — call the facility if urgent</li>",
        "<li><strong>Visitation:</strong> Confirm hours and rules with the facility before you go</li>",
        "</ul>",
        "</div>",
    ]
    return "\n".join(card_lines)


def _template_fallback(county: str, state: str, state_abbr: str,
                       real_links: dict = None,
                       primary_keyword: str = None) -> str:
    """Template-based page body — never uses Google Search as official links."""
    if real_links is None:
        real_links = _get_real_links(county, state, state_abbr)
    if primary_keyword is None:
        primary_keyword = get_primary_keyword(county, state, state_abbr)
    info_card = _county_info_card(county, state, real_links)
    addr = real_links.get("jail_address", "")
    phone = real_links.get("jail_phone", "")
    jail_name = real_links.get("jail_name", f"{county} County Jail")
    sheriff_name = real_links.get("sheriff_name", f"{county} County Sheriff's Office")
    phone_answer = f" You can also call {phone} to speak with staff." if phone else ""
    addr_answer = f" The main facility is located at {addr}." if addr else ""

    roster = real_links.get("inmate_search") or ""
    primary = real_links.get("sheriff_search") or ""
    doc_url = real_links.get("doc_url") or ""
    fbop = real_links.get("fbop") or "https://www.bop.gov/inmateloc/"
    court = real_links.get("court_search") or ""

    if roster:
        step1 = f'<li>Open the {_safe_href(roster, f"{county} County official inmate roster")}</li>'
        how_find = (
            f"<p>Use the {_safe_href(roster, f'official {county} County inmate roster')} "
            f"or call the jail directly.{phone_answer} Records often lag 2–8 hours after booking.</p>"
        )
        contact_roster = f"<li>{_safe_href(roster, f'{county} County inmate roster')}</li>"
    else:
        step1 = (
            f"<li>Contact the {sheriff_name}"
            + (f" at {phone}" if phone else "")
            + " and ask for the current inmate / booking desk process "
            "(many counties do not publish a public web roster)</li>"
        )
        how_find = (
            f"<p>There is no verified public online roster URL on file for {county} County. "
            f"Call the {sheriff_name}"
            + (f" at {phone}" if phone else "")
            + f" or use the {_safe_href(doc_url, f'{state} Department of Corrections')} site "
            f"for state custody. We do not treat web search results as official jail records.</p>"
        )
        contact_roster = f"<li>{sheriff_name} — call the facility for booking status</li>"

    court_line = ""
    if court:
        court_line = (
            f'<p>For hearing schedules, contact the {_safe_href(court, f"{county} County court")}.</p>'
        )
    else:
        court_line = (
            f"<p>For hearing schedules, contact the {county} County clerk of court or "
            f"{sheriff_name} for the correct court division.</p>"
        )

    return f"""<h1>{primary_keyword}</h1>
{info_card}
<p>Looking for someone in {county} County, {state}? This guide explains how to check
{county} County jail records, contact the facility, and understand booking and bail
in {county} County, {state} — using official government sources when available.</p>

<h2>How to Search {county} County Jail Records</h2>
<ol>
  {step1}
  <li>Provide the person's full name; try alternate spellings if needed</li>
  <li>Review booking date, charges, and bond information when published</li>
  <li>Note any booking number before calling the facility</li>
  <li>If nothing appears yet, wait for the next update cycle or call the jail</li>
</ol>

<h2>Official {county} County Resources</h2>
<ul class="resource-list">
{real_links['links_html']}
</ul>

<h2>Bail Bond Information for {county} County</h2>
<p>After booking into {county} County jail, a judge typically sets bail at arraignment
(often within 24–72 hours). Families often work with a licensed bail bondsman. A common
commercial bond fee is about <strong>10% of the bail amount</strong> (non-refundable).
Example: $10,000 bail → roughly $1,000 premium, subject to local rules.</p>
<p>If the person cannot afford bail, they may request a reduction hearing or public defender.
{court_line}</p>

<h2>Visitation Rules at {county} County Jail</h2>
<p>Policies vary. Before visiting {jail_name}, confirm:</p>
<ul>
  <li><strong>Approved ID:</strong> Government-issued photo ID</li>
  <li><strong>Hours:</strong> Call {sheriff_name} for the current schedule</li>
  <li><strong>Dress code:</strong> Facilities restrict clothing that resembles uniforms</li>
  <li><strong>Video visits:</strong> Many jails offer remote options — ask when you call</li>
  <li><strong>Children:</strong> Minors usually need an accompanying adult</li>
</ul>

<h2>What to Expect After Arrest in {county} County</h2>
<p>Typical steps after arrest in {county} County:</p>
<ol>
  <li><strong>Booking</strong> — fingerprints, photo, property inventory</li>
  <li><strong>Medical screening</strong> — before general population housing</li>
  <li><strong>Classification</strong> — housing based on charges and history</li>
  <li><strong>Arraignment</strong> — first court appearance; bail often set here</li>
  <li><strong>Transfer</strong> — serious cases may move to a state facility</li>
</ol>

<h2>How to Contact {county} County Jail</h2>
<p>For status, bail, visitation, or medical questions, contact {sheriff_name} directly.</p>
<ul>
  {contact_roster}
  <li>{_safe_href(doc_url, f"{state} Department of Corrections")}</li>
  <li>{_safe_href(fbop, "Federal Bureau of Prisons locator")}</li>
</ul>

<h2>Frequently Asked Questions — {county} County Inmate Lookup</h2>

<h3>How do I find out if someone is in {county} County jail?</h3>
{how_find}

<h3>How long does booking take in {county} County?</h3>
<p>Booking often takes 2–8 hours depending on volume. Weekends and holidays can delay
when a name appears in any published system.</p>

<h3>Can I visit an inmate at {county} County jail?</h3>
<p>Usually yes if the facility allows visits and the person is eligible.{addr_answer}
Contact {jail_name} for hours, ID rules, and dress code. Video visitation may be available.</p>

<h3>What if the person is not in the county jail system?</h3>
<p>They may be in state custody — check the {_safe_href(doc_url, f"{state} DOC")}.
For federal charges use the {_safe_href(fbop, "BOP inmate locator")}.</p>

<h3>How do I send money to an inmate in {county} County?</h3>
<p>Most facilities use a commissary vendor (for example JPay, Securus, or Access Corrections).
Confirm the vendor and limits with {jail_name} before sending funds.</p>"""



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


def run(counties: list, output_dir: Path, delay: float = 0.5, force: bool = False):
    """Generate pages for the given county list."""
    # Write county pages to a subdirectory so they don't clobber build_site.py output
    county_dir = output_dir / "counties"
    county_dir.mkdir(parents=True, exist_ok=True)
    built = []
    total = len(counties)

    for i, (county, state, state_abbr) in enumerate(counties, 1):
        filename = f"{county.lower().replace(' ', '-')}-county-{state.lower().replace(' ', '-')}-inmate-lookup.html"
        out_path = county_dir / filename

        if out_path.exists() and not force:
            print(f"  [{i}/{total}] SKIP {county} County, {state} (exists)")
            built.append((county, state, state_abbr))
            continue

        print(f"  [{i}/{total}] Generating {county} County, {state}...")
        primary_keyword = get_primary_keyword(county, state, state_abbr)
        body = generate_page_content(county, state, state_abbr, primary_keyword)

        # ── Build all template variables ───────────────────────────────────────
        slug = filename  # relative URL path
        # Description: 100-165 chars (Google sweet spot). Old template was 199+ chars (-5 meta pts).
        description = (f"Free {county} County {state} inmate lookup. "
                       f"Official sheriff records, bail bond info, visitation rules, and booking details.")
        state_abbr_lower = state_abbr.lower()
        real_links = _get_real_links(county, state, state_abbr)

        # FAQ schema entries (mirror the 5 FAQ H3s in the body)
        faq_items = [
            {"q": f"How do I find out if someone is in {county} County jail?",
             "a": f"Use the official {county} County Sheriff's Office inmate search or call the jail directly. Records update every 2-8 hours after booking."},
            {"q": f"How long does booking take in {county} County?",
             "a": "Booking typically takes 2-8 hours. During weekends and holidays it may take longer before a record appears in the online search system."},
            {"q": f"Can I visit an inmate at {county} County jail?",
             "a": f"Yes. Contact the {county} County Sheriff's Office for current visitation hours, approved ID requirements, and dress code rules."},
            {"q": f"What if the person is not in the county jail system?",
             "a": f"They may have been transferred to a state facility. Check the {state} Department of Corrections inmate locator. For federal charges, use the Federal Bureau of Prisons locator."},
            {"q": f"How do I send money to an inmate in {county} County?",
             "a": f"Most {county} County facilities use a third-party commissary service such as JPay, Securus, or Access Corrections. Contact the jail directly for the service they use."},
        ]
        import json as _json
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "FAQPage",
                    "mainEntity": [
                        {"@type": "Question", "name": item["q"],
                         "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                        for item in faq_items
                    ]
                },
                {
                    "@type": "WebPage",
                    "name": primary_keyword,
                    "description": description,
                    "url": f"https://jailinmate.net/{slug}",
                    "publisher": {
                        "@type": "Organization",
                        "name": "jailinmate.net",
                        "url": "https://jailinmate.net"
                    }
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://jailinmate.net/"},
                        {"@type": "ListItem", "position": 2, "name": state, "item": f"https://jailinmate.net/states/{state_abbr_lower}.html"},
                        {"@type": "ListItem", "position": 3, "name": f"{county} County", "item": f"https://jailinmate.net/{slug}"}
                    ]
                }
            ]
        }
        schema_json = _json.dumps(schema, indent=2)

        html = HTML_TEMPLATE.format(
            county=county, state=state, state_abbr=state_abbr,
            state_abbr_lower=state_abbr_lower,
            title=primary_keyword,
            description=description,
            slug=slug,
            schema_json=schema_json,
            body=body
        )
        # Final guard: never write a page that is missing canonical or schema
        if 'rel="canonical"' not in html or 'application/ld+json' not in html:
            print(f"  SKIP {county},{state} — final HTML missing canonical or schema (template bug?)")
            continue
        out_path.write_text(html, encoding="utf-8")
        built.append((county, state, state_abbr))
        time.sleep(delay)  # Rate limit

    # Do NOT call build_index() — index.html is owned by build_site.py
    print(f"\nDone. Generated {len(built)} county pages -> {county_dir}")
    return built


def strip_noindex_from_dist(dist_dir: Path) -> int:
    """
    Remove <meta name="robots" content="noindex,..."> from all existing HTML pages.
    County pages were generated with an older template that included noindex.
    This tag costs -30 technical SEO points and prevents Google indexing.
    Returns count of files fixed.
    """
    import re
    fixed = 0
    noindex_pattern = re.compile(
        r'<meta\s+name=["\']robots["\'][^>]*noindex[^>]*>\s*\n?',
        re.IGNORECASE
    )
    for html_file in dist_dir.rglob('*.html'):
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            if 'noindex' in content.lower():
                cleaned = noindex_pattern.sub('', content)
                if cleaned != content:
                    html_file.write_text(cleaned, encoding='utf-8')
                    fixed += 1
        except Exception as e:
            print(f"  WARN: could not fix {html_file.name}: {e}")
    return fixed


def fix_county_descriptions(dist_dir: Path) -> int:
    """
    Update meta descriptions on all existing county pages to be within 100-165 chars.
    The old template produced 199+ char descriptions, triggering a -5 meta penalty.
    Matches pages by filename pattern (contains 'inmate-lookup').
    Returns count of files fixed.
    """
    import re
    fixed = 0
    pattern = re.compile(
        r'(<meta\s+name=["\']description["\']\s+content=["\'])([^"\']*)(["\'])',
        re.IGNORECASE
    )
    for html_file in dist_dir.rglob('*.html'):
        if 'inmate-lookup' not in html_file.name:
            continue
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            m = pattern.search(content)
            if not m:
                continue
            old_desc = m.group(2)
            if len(old_desc) <= 165:
                continue  # already fine
            # Extract county/state from the old description pattern
            # Old format: "How to do an inmate lookup in {county} County, {state} — ..."
            county_m = re.match(r'How to do an inmate lookup in (.+?) County, (.+?) —', old_desc)
            if not county_m:
                continue
            county = county_m.group(1)
            state = county_m.group(2)
            new_desc = (f"Free {county} County {state} inmate lookup. "
                        f"Official sheriff records, bail bond info, visitation rules, and booking details.")
            new_content = pattern.sub(
                lambda x: x.group(1) + new_desc + x.group(3),
                content, count=1
            )
            # Also update og:description and twitter:description
            new_content = re.sub(
                r'(<meta\s+property=["\']og:description["\']\s+content=["\'])[^"\']*(["\'])',
                lambda x: x.group(1) + new_desc + x.group(2),
                new_content, flags=re.IGNORECASE
            )
            new_content = re.sub(
                r'(<meta\s+name=["\']twitter:description["\']\s+content=["\'])[^"\']*(["\'])',
                lambda x: x.group(1) + new_desc + x.group(2),
                new_content, flags=re.IGNORECASE
            )
            html_file.write_text(new_content, encoding='utf-8')
            fixed += 1
        except Exception as e:
            print(f'  WARN {html_file.name}: {e}')
    return fixed

    """
    Fix SEO metadata on support pages (about, contact, privacy) that have:
    - Short titles (<30 chars) costing -10 meta points
    - Short descriptions (<100 chars) costing -8 meta points
    - Missing JSON-LD schema costing -60 schema points
    Returns count of files fixed.
    """
    import re
    fixes = {
        'about.html': {
            'title': 'About jailinmate.net — Free County Inmate Lookup Resource',
            'description': 'jailinmate.net provides free links to official county jail inmate records across all 50 US states and 3,100+ counties. Search any county instantly with no registration required.',
            'schema': '{"@context":"https://schema.org","@type":"WebSite","name":"jailinmate.net","url":"https://jailinmate.net","description":"Free directory of official county jail inmate lookup resources across all 50 US states."}',
        },
        'contact.html': {
            'title': 'Contact jailinmate.net — Questions About Inmate Lookup',
            'description': 'Contact jailinmate.net with questions, feedback, or data correction requests. We link only to official government jail record sources across all 3,100+ US counties.',
            'schema': '{"@context":"https://schema.org","@type":"ContactPage","name":"Contact jailinmate.net","url":"https://jailinmate.net/contact.html"}',
        },
        'privacy.html': {
            'description': 'jailinmate.net privacy policy. We do not store personal data, sell information, or track users beyond standard analytics. All inmate search links go to official government sources.',
        },
    }
    fixed = 0
    for filename, updates in fixes.items():
        p = dist_dir / filename
        if not p.exists():
            continue
        try:
            content = p.read_text(encoding='utf-8', errors='ignore')
            changed = False
            if 'title' in updates:
                new_title = f'<title>{updates["title"]}</title>'
                content, n = re.subn(r'<title>[^<]*</title>', new_title, content, flags=re.I)
                if n: changed = True
            if 'description' in updates:
                new_desc = f'content="{updates["description"]}"'
                content, n = re.subn(
                    r'(<meta[^>]+name=["\']description["\'][^>]+content=)["\'][^"\']*["\']',
                    lambda m: m.group(1) + '"' + updates['description'] + '"',
                    content, flags=re.I
                )
                if n: changed = True
            if 'schema' in updates and 'application/ld+json' not in content:
                schema_tag = f'\n<script type="application/ld+json">\n{updates["schema"]}\n</script>'
                content = content.replace('</head>', schema_tag + '\n</head>', 1)
                changed = True
            if changed:
                p.write_text(content, encoding='utf-8')
                fixed += 1
                print(f'  Fixed: {filename}')
        except Exception as e:
            print(f'  WARN: could not fix {filename}: {e}')
    return fixed

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Generate all counties (requires CSV)")
    parser.add_argument("--state", help="Filter by state abbreviation (e.g. TX)")
    parser.add_argument("--count", type=int, default=10, help="Number of counties to generate")
    parser.add_argument("--force", action="store_true", help="Overwrite existing pages (use after template changes)")
    parser.add_argument("--template-only", action="store_true", help="Skip AI; use template body only (bulk regen)")
    parser.add_argument("--strip-noindex", action="store_true", help="Remove noindex robots tags from all existing dist pages")
    parser.add_argument("--fix-support-seo", action="store_true", help="Fix SEO metadata on about/contact/privacy support pages")
    parser.add_argument("--fix-descriptions", action="store_true", help="Shorten over-long meta descriptions on all county pages (>165 chars -> ~130 chars)")
    args = parser.parse_args()

    out = Path(__file__).resolve().parent / "dist"

    if getattr(args, 'strip_noindex', False):
        print("Stripping noindex from all existing pages...")
        fixed = strip_noindex_from_dist(out)
        print(f"Fixed {fixed} pages — noindex removed")
    elif getattr(args, 'fix_support_seo', False):
        print("Fixing SEO metadata on support pages...")
        fixed = fix_support_page_seo(out)
        print(f"Fixed {fixed} support pages — titles/descriptions/schema updated")
    elif getattr(args, 'fix_descriptions', False):
        print("Fixing over-long meta descriptions on county pages...")
        fixed = fix_county_descriptions(out)
        print(f"Fixed {fixed} county pages — descriptions trimmed to 100-165 chars")
    elif args.all:
        # Load from CSV if available
        csv_path = Path(__file__).resolve().parent / "counties.csv"
        if csv_path.exists():
            import csv
            with open(csv_path, encoding="utf-8-sig") as f:
                all_counties = [(r["county"], r["state"], r["state_abbr"]) for r in csv.DictReader(f)]
        else:
            print("No counties.csv found — using sample list")
            all_counties = SAMPLE_COUNTIES
        counties = [c for c in all_counties if not args.state or c[2] == args.state]
    else:
        counties = SAMPLE_COUNTIES[:args.count]
        if args.state:
            counties = [c for c in SAMPLE_COUNTIES if c[2] == args.state]

    if (not getattr(args, 'strip_noindex', False) and not getattr(args, 'fix_support_seo', False)
            and not getattr(args, 'fix_descriptions', False)):
        if getattr(args, 'template_only', False):
            os.environ["SCE_INMATE_TEMPLATE_ONLY"] = "1"
            run(counties, out, force=args.force, delay=0.0)
        else:
            run(counties, out, force=args.force)
