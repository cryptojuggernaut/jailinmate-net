"""Add www.jailinmate.net as a custom domain to the Cloudflare Pages project."""
import truststore; truststore.inject_into_ssl()
import urllib.request, json, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
TOKEN   = os.environ["CLOUDFLARE_API_TOKEN"]
ACCT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCT_ID}/pages/projects/jailinmate-net/domains"
body = json.dumps({"name": "www.jailinmate.net"}).encode()
req = urllib.request.Request(url, data=body, headers={
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
        if data.get("success"):
            d = data["result"]
            print(f"Added: {d['name']} | status: {d.get('status','?')}")
        else:
            print("Failed:", data.get("errors"))
except urllib.error.HTTPError as e:
    data = json.loads(e.read())
    print("Error:", data.get("errors"))
