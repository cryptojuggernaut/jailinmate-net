"""
patch_state_pages.py — Add missing OG tags and JSON-LD schema to all state pages.

State pages have titles, H1, canonical, meta desc — but missing OG + schema.
This patches all 50 in one pass.

Usage: python patch_state_pages.py
"""

import re
from pathlib import Path

DIST = Path("dist/states")
BASE_URL = "https://jailinmate.net"

OG_BLOCK = """
  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{url}">
  <meta property="og:site_name" content="jailinmate.net">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">"""

SCHEMA_BLOCK = """
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "{title}",
    "description": "{description}",
    "url": "{url}",
    "isPartOf": {{"@type": "WebSite", "name": "jailinmate.net", "url": "{base_url}"}}
  }}
  </script>"""


def extract_meta(html: str, name: str) -> str:
    m = re.search(rf'<meta\s+name="{name}"\s+content="([^"]*)"', html)
    return m.group(1) if m else ""


def extract_title(html: str) -> str:
    m = re.search(r"<title>([^<]*)</title>", html)
    return m.group(1).strip() if m else ""


def extract_canonical(html: str) -> str:
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', html)
    return m.group(1) if m else ""


def patch_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8")

    # Already patched?
    if 'property="og:title"' in html:
        return "skipped"

    title = extract_title(html)
    description = extract_meta(html, "description")
    url = extract_canonical(html)

    if not title or not url:
        return "no data"

    og = OG_BLOCK.format(title=title, description=description, url=url)
    schema = SCHEMA_BLOCK.format(
        title=title, description=description, url=url, base_url=BASE_URL
    )

    # Insert OG tags after viewport meta
    html = re.sub(
        r'(<meta name="viewport"[^>]*>)',
        r"\1" + og,
        html, count=1
    )

    # Insert schema before </head>
    html = html.replace("</head>", schema + "\n</head>", 1)

    path.write_text(html, encoding="utf-8")
    return "patched"


def main():
    pages = list(DIST.glob("*.html"))
    print(f"Patching {len(pages)} state pages...\n")
    patched = 0
    for p in sorted(pages):
        result = patch_file(p)
        if result == "patched":
            patched += 1
        print(f"  {result:8}  {p.name}")
    print(f"\nDone: {patched}/{len(pages)} patched")


if __name__ == "__main__":
    main()
