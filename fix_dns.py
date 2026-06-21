"""Add www CNAME + email protection records to jailinmate.net via Cloudflare API."""
import truststore; truststore.inject_into_ssl()
import urllib.request, urllib.error, json, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
TOKEN   = os.environ["CLOUDFLARE_API_TOKEN"]
ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID", "f0ff2c8b1e8b589d016eb6d55896f56e")

BASE = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def cf(method, path="", body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

records = [
    # www → apex (Cloudflare handles the redirect via Pages custom domain)
    {"type": "CNAME", "name": "www", "content": "jailinmate.net", "proxied": True, "ttl": 1},
    # SPF — no email sending from this domain
    {"type": "TXT", "name": "@", "content": "v=spf1 -all", "ttl": 1},
    # DMARC — reject anything claiming to be from jailinmate.net
    {"type": "TXT", "name": "_dmarc", "content": "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s;", "ttl": 1},
]

for rec in records:
    result = cf("POST", "", rec)
    if result.get("success"):
        r = result["result"]
        print(f"  ADDED  {r['type']} {r['name']} -> {r['content']}")
    else:
        errors = result.get("errors", [])
        # Code 81057 = record already exists
        if any(e.get("code") == 81057 for e in errors):
            print(f"  EXISTS {rec['type']} {rec['name']} (skipped)")
        else:
            print(f"  FAILED {rec['type']} {rec['name']}: {errors}")
