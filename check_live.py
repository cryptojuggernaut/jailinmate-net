import truststore; truststore.inject_into_ssl()
import urllib.request, re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

pages = [
    "https://jailinmate.net/counties/los-angeles-county-california-inmate-lookup.html",
    "https://jailinmate.net/counties/harris-county-texas-inmate-lookup.html",
    "https://jailinmate.net/counties/cook-county-illinois-inmate-lookup.html",
    "https://jailinmate.net/counties/ziebach-county-south-dakota-inmate-lookup.html",
    "https://jailinmate.net/",
]

for url in pages:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
            name = url.split("/")[-1][:55] or "homepage"
            canonical  = 'rel="canonical"' in html
            schema     = "application/ld+json" in html
            breadcrumb = "breadcrumb" in html
            no_dead    = 'href="#"' not in html
            no_md      = "```" not in html
            has_h1     = "<h1" in html
            h1_match   = re.search(r"<h1[^>]*>(.*?)</h1>", html)
            h1_text    = h1_match.group(1)[:70] if h1_match else "MISSING"
            print(f"{name}")
            print(f"  HTTP {r.status} | {len(html)} chars | canonical={canonical} schema={schema} breadcrumb={breadcrumb} h1={has_h1} no_dead={no_dead} no_md={no_md}")
            print(f"  H1: {h1_text}")
    except Exception as e:
        print(f"ERROR {url}: {e}")
