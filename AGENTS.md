# Inmate Lookup Site — AGENTS.md
> Updated: 2026-06-04

## Domain
**jailinmate.net** — registered on Cloudflare ✅

## Current Status
- **Phase:** Site built ✅ — deploy to Cloudflare Pages next
- **Domain:** `jailinmate.net` (registered, on Cloudflare nameservers)
- **Built pages:** 57 (index, 50 state pages, about, privacy, contact, sitemap, robots.txt)
- **Dist folder:** `C:\WebAutomation\projects\inmate-lookup-site\dist\`
- **Next blocker:** Create GitHub repo → connect to Cloudflare Pages

## What This Project Is
AdSense-monetized directory site targeting inmate/court records search traffic.
Strategy: hyper-local guide pages (one per US county ~3,000 pages) linking to official sources.
Revenue model: Google AdSense display ads + bail bond affiliate links ($15–50/lead).

## Current Status
- **Phase:** Research complete ✅ — waiting on domain registration
- **Blocker:** No domain registered yet
- **Recommended domains:** `countyjails.com` or `jailroster.com` (~$10–15 on Namecheap)
- **Hosting:** Cloudflare Pages (free static hosting)

## Financial Projections
| Month | Est. Monthly Revenue |
|-------|---------------------|
| 1–3   | $0 (indexing phase) |
| 6     | $150–$400/month |
| 12    | $700–$2,100/month |

## Key Decisions Made
- Do NOT host real inmate data — guide/directory ONLY (legal safety)
- Target "[County Name] inmate lookup" long-tail keywords (3,000 counties)
- Programmatic page generation (one Python script generates all pages)
- AdSense + bail bond affiliate (Afford Bail, Bad Boys Bail Bonds programs)

## Tech Stack
- Static HTML pages (programmatically generated)
- Cloudflare Pages (free CDN + hosting)
- Google AdSense
- Bail bond affiliate program
- No database needed — pure static

## What's Left

- [ ] Submit sitemap.xml to Google Search Console
- [ ] Set up keyword rank tracking in SCE SEO tab (target: "[County] inmate lookup")
- [ ] Generate remaining ~2,940 county pages (queue `county_pages_gen` task in SCE)
- [ ] Apply for Google AdSense (need 3+ months of content indexed first)
- [ ] Apply for bail bond affiliate program (Afford Bail or Bad Boys Bail Bonds)
- [x] Set monthly revenue goal in SCE Goals tab (target: $400/month by month 6)
- [ ] Push dist/ to GitHub repo and connect to Cloudflare Pages deploy hook

## Research Files
- `SCE_platform_spec.md` — niche analysis and research

## Workspace Rules
- Output to files only
- PowerShell syntax
- No clarifying questions
