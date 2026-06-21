# Inmate Lookup Site — AGENTS.md
> Updated: 2026-06-21

## Domain
**jailinmate.net** — registered on Cloudflare ✅

## Current Status
- **Phase:** Live ✅ — 3,100 AI county pages deployed, sitemap submitted to GSC
- **Domain:** `jailinmate.net` (live on Cloudflare Pages, clean URLs active)
- **Built pages:** 3,158 total (3,100 county pages + state pages + core pages)
- **Dist folder:** `C:\WebAutomation\projects\inmate-lookup-site\dist\`
- **GitHub repo:** `cryptojuggernaut/jailinmate-net` (auto-deploys via Cloudflare Pages)
- **Audit:** 3100/3100 county pages pass (audit_pages.py — all checks green)

## What This Project Is
AdSense-monetized directory site targeting inmate/court records search traffic.
Strategy: hyper-local guide pages (one per US county ~3,000 pages) linking to official sources.
Revenue model: Google AdSense display ads + bail bond affiliate links ($15–50/lead).

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

- [x] Submit sitemap.xml to Google Search Console (done 2026-06-21, 3,152 pages discovered)
- [x] Generate all 3,100 county pages with AI content (done 2026-06-21, 3100/3100 audit pass)
- [x] Push dist/ to GitHub repo and connect to Cloudflare Pages (done 2026-06-21)
- [x] Set monthly revenue goal in SCE Goals tab (target: $400/month by month 6)
- [ ] Set up Google Indexing API to accelerate crawl (console.cloud.google.com)
- [ ] Set up keyword rank tracking in SCE SEO tab (target: "[County] inmate lookup")
- [ ] Apply for bail bond affiliate program (Afford Bail or Bad Boys Bail Bonds)
- [ ] Apply for Google AdSense — eligible ~2026-09-21 (domain age gate ~3 months)

## Research Files
- `SCE_platform_spec.md` — niche analysis and research

## Workspace Rules
- Output to files only
- PowerShell syntax
- No clarifying questions
