# jailinmate.net — Cloudflare Pages Deployment

## Domain: jailinmate.net (registered on Cloudflare ✅)

## Deploy Steps

### 1. Push dist/ to GitHub
```powershell
cd C:\WebAutomation\projects\inmate-lookup-site
git init
git add dist/
git commit -m "Initial site build — 57 pages"
git remote add origin https://github.com/YOUR_USER/jailinmate-net.git
git push -u origin main
```

### 2. Connect to Cloudflare Pages
1. Go to https://dash.cloudflare.com → Pages → Create a project
2. Connect GitHub → select `jailinmate-net` repo
3. Build settings:
   - **Framework preset**: None
   - **Build command**: `python build_site.py`
   - **Build output directory**: `dist`
   - **Root directory**: `/`
4. Click Save and Deploy

### 3. Connect your domain
1. Pages project → Custom domains → Add custom domain
2. Enter: `jailinmate.net`
3. Cloudflare auto-configures DNS (already on CF nameservers)

### 4. After deploy — submit to Google
1. https://search.google.com/search-console → Add property → `jailinmate.net`
2. Verify via Cloudflare DNS TXT record
3. Submit sitemap: `https://jailinmate.net/sitemap.xml`
4. Request indexing on homepage

## Apply for AdSense
- URL: https://www.google.com/adsense/start/
- Site must have 10+ pages and real content — ✅ done
- Approval: 1-4 weeks
- Once approved, replace `<!-- Google AdSense placeholder -->` comment in build_site.py

## Generate More County Pages
```powershell
# Generate top counties without AI (fast)
python generate_pages.py --count 50

# Generate all counties (needs counties.csv)
python generate_pages.py --all
```

## Current Status
- [x] Domain registered: jailinmate.net
- [x] 3,158 pages built in dist/ (3,100 AI county pages + state/core pages)
- [x] sitemap.xml generated (3,152 URLs)
- [x] Cloudflare security headers
- [x] GitHub repo created: cryptojuggernaut/jailinmate-net
- [x] Cloudflare Pages connected (auto-deploys on push to main)
- [x] Google Search Console verified + sitemap submitted (2026-06-21, 3,152 pages)
- [x] All county pages pass SEO audit (3100/3100)
- [ ] Google Indexing API set up (speeds up crawl)
- [ ] AdSense applied (eligible ~2026-09-21)
