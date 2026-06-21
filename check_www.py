import truststore; truststore.inject_into_ssl()
import urllib.request, socket

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

# DNS check
try:
    ip = socket.gethostbyname("www.jailinmate.net")
    print("DNS OK:", ip)
except Exception as e:
    print("DNS not resolving yet:", e)

# HTTP check
for url in ["https://www.jailinmate.net/", "https://www.jailinmate.net/counties/los-angeles-county-california-inmate-lookup.html"]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", errors="replace")
            has_canonical = 'rel="canonical"' in html
            has_h1 = "<h1" in html
            print(f"HTTP {r.status} | {len(html)} chars | canonical={has_canonical} h1={has_h1} | {url}")
    except Exception as e:
        print(f"FAIL {url}: {e}")
