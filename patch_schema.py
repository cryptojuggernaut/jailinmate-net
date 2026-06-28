"""
Patch script: 
1. Add JSON-LD WebPage schema to privacy.html, about.html, contact.html
2. Add Terms link to nav and footer on all legal pages
3. Add BreadcrumbList to generator template for future county pages
4. Retrofit BreadcrumbList schema to all existing county pages
"""
import json
from pathlib import Path

DIST = Path(r"C:\WebAutomation\projects\inmate-lookup-site\dist")

# ── TASK 1: Add schema + Terms link to legal pages ────────────────────────────
LEGAL_PAGES = {
    "privacy.html": {
        "name": "Privacy Policy — jailinmate.net",
        "description": "Privacy policy for jailinmate.net — an informational resource linking to official government inmate search tools.",
        "url": "https://jailinmate.net/privacy.html",
        "breadcrumb_name": "Privacy Policy",
        "breadcrumb_slug": "privacy.html",
    },
    "about.html": {
        "name": "About jailinmate.net — Free County Inmate Lookup",
        "description": "About jailinmate.net — a free informational resource that links to official government inmate search tools for all 3,143 US counties.",
        "url": "https://jailinmate.net/about.html",
        "breadcrumb_name": "About",
        "breadcrumb_slug": "about.html",
    },
    "contact.html": {
        "name": "Contact — jailinmate.net",
        "description": "Contact jailinmate.net — questions about our inmate lookup resource, link errors, or privacy concerns.",
        "url": "https://jailinmate.net/contact.html",
        "breadcrumb_name": "Contact",
        "breadcrumb_slug": "contact.html",
    },
}

for filename, meta in LEGAL_PAGES.items():
    path = DIST / filename
    if not path.exists():
        print(f"SKIP {filename} — not found")
        continue
    
    content = path.read_text(encoding="utf-8")
    
    # 1a. Add JSON-LD schema before </head>
    if "application/ld+json" not in content:
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta["name"],
            "description": meta["description"],
            "url": meta["url"],
            "publisher": {
                "@type": "Organization",
                "name": "jailinmate.net",
                "url": "https://jailinmate.net"
            },
            "breadcrumb": {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://jailinmate.net/"},
                    {"@type": "ListItem", "position": 2, "name": meta["breadcrumb_name"], "item": meta["url"]}
                ]
            }
        }
        schema_block = f'\n<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>\n'
        content = content.replace("<meta name=\"google-adsense-account\"", schema_block + "<meta name=\"google-adsense-account\"")
        print(f"  + Added schema to {filename}")
    else:
        print(f"  ~ {filename} already has schema")
    
    # 1b. Add Terms to nav if missing
    if "/terms.html" not in content:
        content = content.replace(
            '<a href="/contact.html">Contact</a>\n  </div>',
            '<a href="/contact.html">Contact</a>\n    <a href="/terms.html">Terms</a>\n  </div>'
        )
        print(f"  + Added Terms nav link to {filename}")
    
    # 1c. Add Terms to footer if missing
    if "Terms of Service" not in content and "/terms.html" not in content:
        content = content.replace(
            '<a href="/contact.html">Contact</a></p>',
            '<a href="/contact.html">Contact</a> &nbsp;·&nbsp; <a href="/terms.html">Terms of Service</a></p>'
        )
        print(f"  + Added Terms footer link to {filename}")
    
    path.write_text(content, encoding="utf-8")

# ── TASK 2: Retrofit BreadcrumbList to all existing county pages ───────────────
print("\nRetrofitting BreadcrumbList to county pages...")

county_dir = DIST / "counties"
county_files = list(county_dir.glob("*.html"))
total = len(county_files)
patched = 0
skipped = 0

for f in county_files:
    content = f.read_text(encoding="utf-8")
    
    # Skip if already has BreadcrumbList
    if "BreadcrumbList" in content:
        skipped += 1
        continue
    
    # Parse county/state from filename: {county}-county-{state}-inmate-lookup.html
    # We need to add BreadcrumbList to the existing @graph in the JSON-LD
    # Strategy: find the existing JSON-LD block and inject BreadcrumbList into @graph
    import re
    
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    if not m:
        skipped += 1
        continue
    
    try:
        existing = json.loads(m.group(1))
    except json.JSONDecodeError:
        skipped += 1
        continue
    
    # Find the WebPage entry to extract url
    page_url = None
    if "@graph" in existing:
        for node in existing["@graph"]:
            if node.get("@type") == "WebPage":
                page_url = node.get("url", "")
                break
    
    if not page_url:
        # Try direct url field
        page_url = existing.get("url", "")
    
    if not page_url:
        skipped += 1
        continue
    
    # Extract state from URL: https://jailinmate.net/counties/{county}-county-{state}-inmate-lookup.html
    slug = page_url.split("/counties/")[-1].replace("-inmate-lookup.html", "")
    # slug is like "los-angeles-county-california"
    parts = slug.split("-county-")
    if len(parts) == 2:
        county_name = parts[0].replace("-", " ").title()
        state_name = parts[1].replace("-", " ").title()
        # Get state abbr from URL to build state page link
        state_slug = parts[1]  # e.g. "california"
    else:
        county_name = "County"
        state_name = "State"
        state_slug = "state"
    
    # Build breadcrumb items
    # We need the state abbr — search in existing content for the state link
    state_link_m = re.search(r'href="/states/([a-z]+)\.html"', content)
    state_abbr = state_link_m.group(1) if state_link_m else state_slug[:2]
    
    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://jailinmate.net/"},
            {"@type": "ListItem", "position": 2, "name": state_name, "item": f"https://jailinmate.net/states/{state_abbr}.html"},
            {"@type": "ListItem", "position": 3, "name": f"{county_name} County", "item": page_url}
        ]
    }
    
    # Inject into @graph or as second graph node
    if "@graph" in existing:
        existing["@graph"].append(breadcrumb)
    else:
        # Wrap in @graph
        existing = {
            "@context": "https://schema.org",
            "@graph": [existing, breadcrumb]
        }
        if "@context" in existing["@graph"][0]:
            del existing["@graph"][0]["@context"]
    
    new_schema = json.dumps(existing, indent=2)
    new_script = f'<script type="application/ld+json">\n{new_schema}\n</script>'
    old_script = m.group(0)
    content = content.replace(old_script, new_script, 1)
    
    f.write_text(content, encoding="utf-8")
    patched += 1

print(f"BreadcrumbList: {patched}/{total} patched, {skipped} skipped")
print("\nAll done!")
