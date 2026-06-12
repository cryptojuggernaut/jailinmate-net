# Google Search Console Setup for jailinmate.net
Generated: 2026-06-12 02:16

## Site Status
- Live URL: https://jailinmate.net
- Sitemap: https://jailinmate.net/sitemap.xml
- Pages indexed in sitemap: 3175

## Step 1: Add Property to Search Console
1. Go to: https://search.google.com/search-console/
2. Click "Add property" → "URL prefix"
3. Enter: https://jailinmate.net
4. Click Continue

## Step 2: Verify Ownership (Fastest Method — Cloudflare DNS)
Since jailinmate.net is on Cloudflare:
1. GSC will show a TXT record like: `google-site-verification=XXXX`
2. Go to Cloudflare Dashboard → DNS → Add Record
   - Type: TXT
   - Name: @ (root)
   - Content: google-site-verification=XXXX
   - TTL: Auto
3. Back in GSC → click Verify
4. Verification should succeed within 1 minute

## Step 3: Submit Sitemap
1. In GSC left menu → Sitemaps
2. Enter: https://jailinmate.net/sitemap.xml
3. Click Submit
4. Status changes from "Pending" → "Success" within ~24h

## Step 4: Request Indexing (Priority Pages)
In GSC → URL Inspection tool, paste and "Request Indexing" for:
- https://jailinmate.net/
- https://jailinmate.net/los-angeles-county-california-inmate-lookup.html
- https://jailinmate.net/harris-county-texas-inmate-lookup.html
- https://jailinmate.net/cook-county-illinois-inmate-lookup.html
- https://jailinmate.net/maricopa-county-arizona-inmate-lookup.html
- https://jailinmate.net/miami-dade-county-florida-inmate-lookup.html

## Automated API Setup (for future automated submissions)
To automate future submissions via SCE:
1. Go to: https://console.cloud.google.com/
2. Create project → Enable "Search Console API" + "Indexing API"
3. Create Service Account → Download JSON key
4. Save to: C:\WebAutomation\sce\google_service_account.json
5. In GSC → Settings → Users → Add user (service account email, Owner)
6. SCE will then auto-submit new pages via indexing API

## AdSense Application (After GSC Verification)
1. Go to: https://www.google.com/adsense/start/
2. Website: https://jailinmate.net
3. Site needs ~10+ content pages (you have 3175) ✓
4. Approval takes 1-4 weeks
5. Once approved: update build_site.py to inject real AdSense code
