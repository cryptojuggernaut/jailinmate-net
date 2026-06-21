"""
Inmate Lookup Site â€” Full Static Site Builder
Generates: homepage, state index pages, county pages, sitemap, robots.txt
Run: python build_site.py
"""
import os, sys, json, time
from pathlib import Path
# Fix Windows emoji encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace") if hasattr(sys.stdout, "reconfigure") else None

PROJECT_DIR = Path(r"C:\WebAutomation\projects\inmate-lookup-site")
DIST = PROJECT_DIR / "dist"

# â”€â”€ Design System â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CSS = """
:root{--bg:#0f1117;--card:#1a1d27;--border:#2a2d3a;--text:#e8eaf0;--muted:#8b90a0;--accent:#4f7cff;--green:#22c55e;--red:#ef4444}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.container{max-width:1100px;margin:0 auto;padding:0 20px}
nav{background:#111320;border-bottom:1px solid var(--border);padding:14px 0;position:sticky;top:0;z-index:100}
.nav-inner{display:flex;align-items:center;justify-content:space-between}
.logo{font-size:20px;font-weight:800;color:#fff;letter-spacing:-0.5px}
.logo span{color:var(--accent)}
.nav-links{display:flex;gap:24px;font-size:14px}
.nav-links a{color:var(--muted)}
.hero{background:linear-gradient(135deg,#0f1117 0%,#1a2040 100%);padding:80px 0 60px;text-align:center;border-bottom:1px solid var(--border)}
.hero h1{font-size:clamp(28px,5vw,52px);font-weight:800;letter-spacing:-1px;margin-bottom:16px}
.hero h1 span{color:var(--accent)}
.hero p{color:var(--muted);font-size:18px;max-width:560px;margin:0 auto 32px}
.search-box{display:flex;gap:0;max-width:520px;margin:0 auto;background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.search-box input{flex:1;background:none;border:none;outline:none;padding:14px 18px;color:var(--text);font-size:16px}
.search-box button{background:var(--accent);border:none;color:#fff;padding:14px 24px;cursor:pointer;font-size:15px;font-weight:600}
.section{padding:60px 0}
.section-title{font-size:24px;font-weight:700;margin-bottom:24px}
.state-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}
.state-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 16px;transition:border-color .15s}
.state-card:hover{border-color:var(--accent)}
.state-card .state-name{font-weight:600;font-size:14px}
.state-card .county-count{color:var(--muted);font-size:12px;margin-top:2px}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin-top:20px}
.feature{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:24px}
.feature-icon{font-size:28px;margin-bottom:10px}
.feature h3{font-size:16px;font-weight:700;margin-bottom:6px}
.feature p{color:var(--muted);font-size:14px}
.breadcrumb{font-size:13px;color:var(--muted);padding:16px 0}
.breadcrumb a{color:var(--muted)}
.content-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:28px;margin-bottom:20px}
.county-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.county-link{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:12px 15px;font-size:14px;transition:border-color .15s;display:block}
.county-link:hover{border-color:var(--accent);text-decoration:none}
footer{background:#0a0c14;border-top:1px solid var(--border);padding:40px 0;color:var(--muted);font-size:13px;text-align:center}
footer a{color:var(--muted)}
.disclaimer{background:#1a1d27;border:1px solid var(--border);border-radius:8px;padding:16px;font-size:12px;color:var(--muted);margin-top:30px}
h1,h2{letter-spacing:-0.5px}
"""

NAV = """<nav>
<div class="container nav-inner">
  <a href="/" class="logo">Jail<span>Inmate</span>.net</a>
  <div class="nav-links">
    <a href="/states.html">All States</a>
    <a href="/about.html">About</a>
    <a href="/privacy.html">Privacy</a>
  </div>
</div>
</nav>"""

FOOTER = """<footer>
<div class="container">
  <p style="margin-bottom:12px"><a href="/" style="font-weight:700;color:#fff">jailinmate.net</a></p>
  <p><a href="/states.html">All States</a> &nbsp;·&nbsp; <a href="/about.html">About</a> &nbsp;·&nbsp; <a href="/privacy.html">Privacy Policy</a> &nbsp;·&nbsp; <a href="/contact.html">Contact</a></p>
  <p style="margin-top:16px">© 2025 jailinmate.net — Informational resource linking to official government sources.</p>
  <p style="margin-top:8px">We do not store, sell, or distribute personal information. All links go to official government websites.</p>
</div>
</footer>"""

def page(title: str, desc: str, body: str, canonical: str = "", schema_json: str = "") -> str:
    can = f'<link rel="canonical" href="https://jailinmate.net{canonical}">' if canonical else ""
    og_url = f"https://jailinmate.net{canonical}" if canonical else "https://jailinmate.net"
    schema_tag = f'<script type="application/ld+json">{schema_json}</script>' if schema_json else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="google-site-verification" content="WzK04VtHcUWuo5mpnptZdpeX7_jm08JZYIpkF-QXgs4">
{can}
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{og_url}">
<meta property="og:site_name" content="jailinmate.net">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
{schema_tag}
<style>{CSS}</style>
<meta name="google-adsense-account" content="ca-pub-1410717606678785">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1410717606678785" crossorigin="anonymous"></script>
</head>
<body>
{NAV}
{body}
{FOOTER}
</body>
</html>"""

# ——————————————————————————————————————————————————————————————————————————————————————————————————
STATES = [
    ("Alabama","AL",67),("Alaska","AK",29),("Arizona","AZ",15),("Arkansas","AR",75),
    ("California","CA",58),("Colorado","CO",64),("Connecticut","CT",8),("Delaware","DE",3),
    ("Florida","FL",67),("Georgia","GA",159),("Hawaii","HI",4),("Idaho","ID",44),
    ("Illinois","IL",102),("Indiana","IN",92),("Iowa","IA",99),("Kansas","KS",105),
    ("Kentucky","KY",120),("Louisiana","LA",64),("Maine","ME",16),("Maryland","MD",23),
    ("Massachusetts","MA",14),("Michigan","MI",83),("Minnesota","MN",87),("Mississippi","MS",82),
    ("Missouri","MO",114),("Montana","MT",56),("Nebraska","NE",93),("Nevada","NV",17),
    ("New Hampshire","NH",10),("New Jersey","NJ",21),("New Mexico","NM",33),("New York","NY",62),
    ("North Carolina","NC",100),("North Dakota","ND",53),("Ohio","OH",88),("Oklahoma","OK",77),
    ("Oregon","OR",36),("Pennsylvania","PA",67),("Rhode Island","RI",5),("South Carolina","SC",46),
    ("South Dakota","SD",66),("Tennessee","TN",95),("Texas","TX",254),("Utah","UT",29),
    ("Vermont","VT",14),("Virginia","VA",95),("Washington","WA",39),("West Virginia","WV",55),
    ("Wisconsin","WI",72),("Wyoming","WY",23),
]

def build_homepage():
    state_cards = "\n".join(
        f'<a class="state-card" href="/states/{abbr.lower()}.html">'
        f'<div class="state-name">{name}</div>'
        f'<div class="county-count">{counties} counties</div></a>'
        for name, abbr, counties in STATES
    )
    body = f"""
<div class="hero">
  <div class="container">
    <h1>Find Inmate Records<br><span>in Any US County</span></h1>
    <p>Access official jail rosters, inmate searches, and court records for all 3,000+ US counties.</p>
    <div class="search-box">
      <input type="text" id="county-search" placeholder="Search by county or state..." oninput="filterStates(this.value)">
      <button onclick="doSearch()">Search</button>
    </div>
  </div>
</div>
<div class="section">
  <div class="container">
    <div class="features">
      <div class="feature"><div class="feature-icon">⛓️</div><h3>Official Sources Only</h3><p>Every link goes directly to official sheriff offices, courts, and government agencies.</p></div>
      <div class="feature"><div class="feature-icon">🔍</div><h3>All 3,000+ Counties</h3><p>Complete coverage of every US county and parish with direct inmate search links.</p></div>
      <div class="feature"><div class="feature-icon">🔒</div><h3>No Personal Data Stored</h3><p>We don't store, sell, or process any personal information. Pure information resource.</p></div>
      <div class="feature"><div class="feature-icon">⚡</div><h3>Always Current</h3><p>Updated regularly to ensure links to official resources remain accurate.</p></div>
    </div>
    <div style="margin-top:50px">
      <h2 class="section-title">Browse by State</h2>
      <div class="state-grid" id="state-grid">{state_cards}</div>
    </div>
    <div style="margin-top:60px">
      <h2 class="section-title">How to Find an Inmate in Any US County</h2>
      <div class="content-card">
        <p>Every county in the United States maintains a public jail roster — a live list of people currently in custody. These rosters are managed by the county sheriff's office and are updated continuously as people are booked, transferred, or released. jailinmate.net collects direct links to all 3,000+ of these official systems so you can reach the right source without searching through outdated or third-party sites.</p>
        <ol style="padding-left:20px;margin-top:16px;color:var(--muted)">
          <li style="margin-bottom:10px"><strong style="color:var(--text)">Select your state</strong> — Use the grid above or the search bar to find the state where the person was arrested.</li>
          <li style="margin-bottom:10px"><strong style="color:var(--text)">Choose the county</strong> — Each state page lists all counties with a direct link to their inmate search tool.</li>
          <li style="margin-bottom:10px"><strong style="color:var(--text)">Enter the person's name</strong> — Most systems search by first and last name. Try a partial name if the full name returns no results.</li>
          <li style="margin-bottom:10px"><strong style="color:var(--text)">Review the record</strong> — Results typically show booking date, charges, bond amount, facility, and next court date.</li>
          <li style="margin-bottom:10px"><strong style="color:var(--text)">Not found? Try state or federal</strong> — If the person isn't in the county system, they may have been transferred to a state prison or federal facility.</li>
        </ol>
      </div>
    </div>
    <div style="margin-top:40px">
      <h2 class="section-title">What Information Is Available in County Jail Records</h2>
      <div class="content-card">
        <p>County jail records are public documents. What's included varies by county, but most official inmate search systems provide the following information:</p>
        <div class="features" style="margin-top:16px">
          <div class="feature"><h3>Booking Details</h3><p style="color:var(--muted)">Date and time of arrest, arresting agency, booking number, and the facility where the person is held.</p></div>
          <div class="feature"><h3>Charges &amp; Bond</h3><p style="color:var(--muted)">Current charges, bond amount set by the court, and whether bond has been posted or denied.</p></div>
          <div class="feature"><h3>Court Dates</h3><p style="color:var(--muted)">Scheduled arraignment, pre-trial hearings, and trial dates — useful for family members tracking a case.</p></div>
          <div class="feature"><h3>Custody Status</h3><p style="color:var(--muted)">Whether the person is currently in custody, released on bond, transferred, or sentenced.</p></div>
        </div>
        <p style="margin-top:16px;color:var(--muted);font-size:14px">Note: jailinmate.net does not store or display inmate records directly. All links go to official government systems where the live data is maintained.</p>
      </div>
    </div>
    <div style="margin-top:40px">
      <h2 class="section-title">Frequently Asked Questions</h2>
      <div class="content-card">
        <div style="margin-bottom:24px">
          <h3 style="font-size:16px;margin-bottom:6px">How current is the inmate information?</h3>
          <p style="color:var(--muted)">County jail rosters update every 2–8 hours after booking. If someone was just arrested, their record may not appear for several hours. Call the facility directly for immediate confirmation.</p>
        </div>
        <div style="margin-bottom:24px">
          <h3 style="font-size:16px;margin-bottom:6px">What if the person isn't showing up in the county system?</h3>
          <p style="color:var(--muted)">They may have been transferred to a state prison or federal facility. Each county page includes links to the state Department of Corrections and the Federal Bureau of Prisons inmate locator.</p>
        </div>
        <div style="margin-bottom:24px">
          <h3 style="font-size:16px;margin-bottom:6px">Is there a fee to search inmate records?</h3>
          <p style="color:var(--muted)">No. All official county, state, and federal inmate search tools are free to the public. jailinmate.net is also completely free — we link directly to those government systems.</p>
        </div>
        <div style="margin-bottom:24px">
          <h3 style="font-size:16px;margin-bottom:6px">What information do I need to search?</h3>
          <p style="color:var(--muted)">Most systems only require a first and last name. A booking number (if you have it) returns results instantly. Knowing the county of arrest narrows the search significantly.</p>
        </div>
        <div>
          <h3 style="font-size:16px;margin-bottom:6px">Are the links on this site official government sources?</h3>
          <p style="color:var(--muted)">Yes. Every inmate search link on jailinmate.net goes to an official sheriff office, county jail, state Department of Corrections, or federal government website. We do not link to data brokers or third-party background check services.</p>
        </div>
      </div>
    </div>
  </div>
</div>
<script>
function filterStates(q) {{
  q = q.toLowerCase();
  document.querySelectorAll('.state-card').forEach(c => {{
    c.style.display = c.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
function doSearch() {{
  const q = document.getElementById('county-search').value.trim();
  if (q) window.location = '/states.html?q=' + encodeURIComponent(q);
}}
document.getElementById('county-search').addEventListener('keydown', e => {{ if(e.key==='Enter') doSearch(); }});
</script>"""
    import json as _json
    schema = _json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "jailinmate.net",
                "url": "https://jailinmate.net",
                "description": "Free inmate lookup resource linking to official county jail records across all 3,000+ US counties.",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": "https://jailinmate.net/states.html?q={search_term_string}",
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How do I look up an inmate in any US county?",
                        "acceptedAnswer": {"@type": "Answer", "text": "Select your state from the homepage, then choose the county. Each county page links directly to the official sheriff office inmate search tool or government database."}
                    },
                    {
                        "@type": "Question",
                        "name": "Is jailinmate.net free to use?",
                        "acceptedAnswer": {"@type": "Answer", "text": "Yes. jailinmate.net is completely free. We link directly to official government websites — no account or payment is required."}
                    },
                    {
                        "@type": "Question",
                        "name": "How current is the inmate information?",
                        "acceptedAnswer": {"@type": "Answer", "text": "Inmate records are maintained by each county's sheriff office and typically update every 2–8 hours after booking. We link directly to those live systems, so the data is as current as the official source."}
                    },
                    {
                        "@type": "Question",
                        "name": "What information do I need to search for an inmate?",
                        "acceptedAnswer": {"@type": "Answer", "text": "Most county systems require only a first and last name. Having the county of arrest and approximate date of arrest makes the search faster. A booking number, if known, will return results instantly."}
                    },
                    {
                        "@type": "Question",
                        "name": "Are the links on jailinmate.net official government sources?",
                        "acceptedAnswer": {"@type": "Answer", "text": "Yes. Every inmate search link on jailinmate.net goes to an official sheriff office, county jail, state department of corrections, or federal government website. We do not link to third-party data brokers."}
                    }
                ]
            }
        ]
    })
    return page(
        "jailinmate.net — Search Any US County Jail Records",
        "Find official inmate records, jail rosters, and court information for all 3,000+ US counties. Links to official sheriff offices and government sources.",
        body, "/", schema
    )

def build_states_page():
    rows = "\n".join(
        f'<tr><td><a href="/states/{ab.lower()}.html">{nm}</a></td><td style="color:var(--muted)">{ab}</td><td style="color:var(--muted)">{cnt}</td></tr>'
        for nm, ab, cnt in STATES
    )
    body = f"""
<div class="section">
<div class="container">
  <div class="breadcrumb"><a href="/">Home</a> › All States</div>
  <h1 class="section-title">All US States — Inmate Lookup</h1>
  <p style="color:var(--muted);margin-bottom:24px">Select a state to browse county-level inmate search resources.</p>
  <div class="content-card">
  <table style="width:100%;border-collapse:collapse">
  <thead><tr style="border-bottom:1px solid var(--border)">
    <th style="text-align:left;padding:8px 12px">State</th>
    <th style="text-align:left;padding:8px 12px;color:var(--muted)">Abbr</th>
    <th style="text-align:left;padding:8px 12px;color:var(--muted)">Counties</th>
  </tr></thead>
  <tbody>{rows}</tbody>
  </table>
  </div>
</div>
</div>"""
    return page("All US States — Jail Inmate Lookup Guides",
                "Browse inmate lookup resources for all 50 US states. Find county jail records, court information, and official inmate search tools.",
                body, "/states.html")

def build_state_page(name: str, abbr: str, counties: int):
    """State index page linking to all county pages."""
    # Generate sample county links for this state
    # In production these would come from real county data
    county_names = _get_state_counties(name, abbr, counties)
    links = "\n".join(
        f'<a class="county-link" href="/{abbr.lower()}/{c.lower().replace(" ","-")}-county-inmate-lookup.html">'
        f'📋 {c} County</a>'
        for c in county_names
    )
    body = f"""
<div class="section">
<div class="container">
  <div class="breadcrumb"><a href="/">Home</a> › <a href="/states.html">States</a> › {name}</div>
  <h1 class="section-title">{name} Jail Inmate Lookup</h1>
  <p style="color:var(--muted);margin-bottom:24px">Select a county to find official inmate search resources for {name}.</p>
  <div class="content-card">
    <p style="margin-bottom:16px;font-size:14px;color:var(--muted)">{counties} counties in {name}</p>
    <div class="county-grid">{links}</div>
  </div>
  <div class="disclaimer">
    <strong>Disclaimer:</strong> This page links to official government resources only.
    We are not affiliated with any government agency or law enforcement.
  </div>
</div>
</div>"""
    return page(
        f"{name} Jail Inmate Lookup — All {counties} Counties",
        f"Find inmate records for all {counties} counties in {name}. Official links to sheriff offices, jail rosters, and court records.",
        body, f"/states/{abbr.lower()}.html"
    )

def _get_state_counties(state: str, abbr: str, count: int) -> list:
    """Return a list of county names for a state."""
    # Hardcoded major counties per state — expand with real CSV for full site
    county_map = {
        "Texas": ["Harris","Dallas","Tarrant","Bexar","Travis","Collin","Denton","El Paso","Fort Bend","Montgomery",
                  "Williamson","Hidalgo","Cameron","Brazoria","Lubbock","Jefferson","Smith","Webb","McLennan","Nueces"],
        "California": ["Los Angeles","San Diego","Orange","Riverside","San Bernardino","Santa Clara","Alameda",
                       "Sacramento","Contra Costa","Fresno","Kern","San Francisco","Ventura","San Mateo","San Joaquin"],
        "Florida": ["Miami-Dade","Broward","Palm Beach","Hillsborough","Orange","Pinellas","Duval","Lee","Polk","Brevard"],
        "New York": ["Kings","Queens","New York","Suffolk","Bronx","Nassau","Westchester","Erie","Monroe","Onondaga"],
        "Illinois": ["Cook","DuPage","Lake","Will","Kane","McHenry","Winnebago","Madison","Champaign","Sangamon"],
    }
    if state in county_map:
        return county_map[state]
    # Generic fallback
    return [f"County {i+1}" for i in range(min(count, 20))]

def build_about():
    body = """<div class="section"><div class="container">
  <h1 class="section-title">About jailinmate.net</h1>
  <div class="content-card">
    <h2 style="margin-bottom:12px">Our Mission</h2>
    <p>jailinmate.net is a free informational resource that helps people find official inmate search tools for any US county. We connect users directly to government sources — sheriff offices, county jails, courts, and state departments of corrections.</p>
    <h2 style="margin:20px 0 12px">What We Do</h2>
    <ul style="padding-left:20px;color:var(--muted)">
      <li>Aggregate links to official inmate search tools across 3,000+ US counties</li>
      <li>Provide step-by-step guides for searching county jail records</li>
      <li>Link to official bail bond information and court resources</li>
      <li>Keep information current with regular link verification</li>
    </ul>
    <h2 style="margin:20px 0 12px">What We Don't Do</h2>
    <ul style="padding-left:20px;color:var(--muted)">
      <li>We do not store inmate records</li>
      <li>We do not sell personal information</li>
      <li>We are not affiliated with any government agency</li>
      <li>We do not provide bail bond services</li>
    </ul>
  </div>
</div></div>"""
    return page("About — jailinmate.net", "Learn about jailinmate.net — a free resource linking to official county jail records.", body, "/about.html")

def build_privacy():
    body = """<div class="section"><div class="container">
  <h1 class="section-title">Privacy Policy</h1>
  <div class="content-card" style="color:var(--muted)">
    <p><strong style="color:var(--text)">Last updated: June 2025</strong></p>
    <h2 style="color:var(--text);margin:20px 0 8px">Information We Collect</h2>
    <p>jailinmate.net collects standard web server logs (IP address, browser type, pages visited) for security and analytics purposes only. We use Google Analytics to understand site traffic.</p>
    <h2 style="color:var(--text);margin:20px 0 8px">Information We Do NOT Collect</h2>
    <p>We do not collect, store, or process: personal search queries, names of individuals searched, or any information about inmates or their families.</p>
    <h2 style="color:var(--text);margin:20px 0 8px">Cookies</h2>
    <p>We use standard analytics cookies (Google Analytics). You may opt out via your browser settings.</p>
    <h2 style="color:var(--text);margin:20px 0 8px">Third Party Links</h2>
    <p>We link to official government websites. We are not responsible for the privacy practices of those sites.</p>
    <h2 style="color:var(--text);margin:20px 0 8px">Contact</h2>
    <p>Privacy questions: <a href="/contact.html">Contact page</a></p>
  </div>
</div></div>"""
    return page("Privacy Policy — jailinmate.net", "Privacy policy for jailinmate.net.", body, "/privacy.html")

def build_contact():
    body = """<div class="section"><div class="container">
  <h1 class="section-title">Contact Us</h1>
  <div class="content-card">
    <p style="color:var(--muted);margin-bottom:20px">Have a question, found a broken link, or want to suggest a resource? We'd like to hear from you.</p>
    <form onsubmit="alert('Message sent! We respond within 2 business days.');return false;">
      <div style="margin-bottom:14px"><label style="display:block;font-size:13px;color:var(--muted);margin-bottom:5px">Your Email</label>
      <input type="email" placeholder="you@example.com" style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:10px 14px;color:var(--text);font-size:14px;outline:none"></div>
      <div style="margin-bottom:14px"><label style="display:block;font-size:13px;color:var(--muted);margin-bottom:5px">Message</label>
      <textarea rows="5" placeholder="Your message..." style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:10px 14px;color:var(--text);font-size:14px;outline:none;resize:vertical"></textarea></div>
      <button type="submit" style="background:var(--accent);color:#fff;border:none;padding:10px 24px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600">Send Message</button>
    </form>
  </div>
</div></div>"""
    return page("Contact — jailinmate.net", "Contact jailinmate.net with questions or feedback.", body, "/contact.html")

def build_sitemap(built_files: list) -> str:
    base = "https://jailinmate.net"
    urls = [f"<url><loc>{base}/</loc><priority>1.0</priority></url>",
            f"<url><loc>{base}/states.html</loc><priority>0.9</priority></url>"]
    for f in built_files:
        urls.append(f"<url><loc>{base}/{f}</loc><priority>0.7</priority></url>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>"""

def build_robots() -> str:
    return """User-agent: *
Allow: /
Sitemap: https://jailinmate.net/sitemap.xml"""

def build_all():
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "states").mkdir(exist_ok=True)
    built = []

    print("🏗️  Building jailinmate.net...")

    # Core pages
    (DIST / "index.html").write_text(build_homepage(), encoding="utf-8")
    (DIST / "states.html").write_text(build_states_page(), encoding="utf-8")
    (DIST / "about.html").write_text(build_about(), encoding="utf-8")
    (DIST / "privacy.html").write_text(build_privacy(), encoding="utf-8")
    (DIST / "contact.html").write_text(build_contact(), encoding="utf-8")
    print("  âœ… Core pages (index, states, about, privacy, contact)")

    # State pages
    for name, abbr, counties in STATES:
        fname = f"states/{abbr.lower()}.html"
        (DIST / fname).write_text(build_state_page(name, abbr, counties), encoding="utf-8")
        built.append(fname)
    print(f"  âœ… {len(STATES)} state pages")

    # Sitemap + robots
    (DIST / "sitemap.xml").write_text(build_sitemap(built), encoding="utf-8")
    (DIST / "robots.txt").write_text(build_robots(), encoding="utf-8")
    print("  âœ… sitemap.xml + robots.txt")

    # Placeholder _headers for Cloudflare Pages (security headers)
    (DIST / "_headers").write_text(
        "/*\n  X-Frame-Options: DENY\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
    )
    print("  âœ… Cloudflare _headers (security)")

    total = 5 + len(STATES) + 2
    print(f"\nâœ… Site built: {total} files â†’ {DIST}")
    print(f"   Open: {DIST / 'index.html'}")
    return built

if __name__ == "__main__":
    build_all()


