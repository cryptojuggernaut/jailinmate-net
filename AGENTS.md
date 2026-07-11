# Inmate Lookup Site — AGENTS.md
> Updated: 2026-07-06

## ⛔ MONETIZATION LOCK — READ BEFORE ANY TASK

```
launched_at:          2026-06-21
adsense_eligible_at:  2026-09-21   ← DO NOT apply before this date
adsense_applied_at:   null
adsense_approved_at:  null
```

**AdSense was REJECTED on 2026-06-29 for "low value content / thin content."**
**DO NOT attempt AdSense, ads, or monetization until 2026-09-21 AND all compliance items below are green.**

CEO → do NOT queue tasks mentioning: adsense, monetize, ad_setup, revenue milestones, ad units.
Full rejection analysis: `projects/inmate-lookup-site/ADSENSE_REJECTION.md`

### Why it was rejected
1. County pages are 95% identical template — Google flags this as thin/doorway pages
2. "Official" links used `google.com/search?q=...` URLs — not real `.gov` sheriff links
3. No unique value-add per county — no address, phone, hours, or real local data

### Content Fix Plan (must complete BEFORE 2026-09-21)
- [ ] **Week 1–4:** Research and add real sheriff URLs for top 500 counties (priority: most-searched)
- [ ] **Week 2–6:** Add unique content block per page: jail address, phone, visiting hours, bail info
- [ ] **Week 4–8:** Add FAQ section per county (at least 3 Q&A pairs, county-specific)
- [ ] **Week 6–10:** Add state-level resource pages with aggregated county data + statistics
- [ ] **Week 8–12:** Verify 300+ word count on every county page, no duplicate blocks
- [ ] **Before applying:** All pages pass `qa_loop_agent.py` compliance check

---

## Google AdSense Compliance Checklist (enforce before every deploy)

### Required Pages — ALL must exist and be non-empty:
- [ ] `/privacy-policy` — mentions Google AdSense, Analytics, cookie consent
- [ ] `/terms-of-service` — user agreement, disclaimer of liability
- [ ] `/about` — who runs the site, mission statement
- [ ] `/contact` — working contact method (form or email)
- [ ] `/disclaimer` — "This site provides public records information for informational purposes only"
- [ ] `/remove-my-information` — removal request process for individuals

### Content Quality Rules (every page):
- [ ] ≥ 300 words of unique content per county page (NO copy-paste between counties)
- [ ] Real `.gov` or official jail/sheriff URL linked (not Google search URL)
- [ ] County-specific data: jail name, address, phone number, bail bond info
- [ ] `<title>` = "[County] County [State] Inmate Lookup | JailInmate.net" (unique per page)
- [ ] `<meta description>` unique per page, ≤ 160 chars, natural language
- [ ] One `<h1>` per page
- [ ] Internal links to state page and related counties
- [ ] FAQ schema markup (`@type: FAQPage`) on each county page

### Technical Compliance:
- [ ] robots.txt allows Googlebot
- [ ] sitemap.xml valid and submitted to GSC
- [ ] All pages return 200 (no 404s in sitemap)
- [ ] HTTPS enforced (Cloudflare handles this ✓)
- [ ] Mobile responsive (viewport meta present ✓)
- [ ] Core Web Vitals: LCP < 2.5s, CLS < 0.1, INP < 200ms
- [ ] No broken internal links

### Content Policy (never violate):
- ❌ No SSNs, DOBs, or financial data displayed
- ❌ No content implying guilt ("criminal", "felon") — use "inmate", "detainee"
- ❌ No scraped content from other sites
- ❌ No auto-generated content that provides no user value
- ❌ No deceptive ad placements or layouts that mimic content
- ✓ Always show: "Information sourced from public records. For official records contact your county jail directly."

---

## Domain
**jailinmate.net** — registered on Cloudflare ✓.

## Current Status
- **Phase:** Live ✓ — 3,100 AI county pages deployed, sitemap submitted to GSC
- **Domain:** `jailinmate.net` (live on Cloudflare Pages, clean URLs active)
- **Built pages:** 3,158 total (3,100 county + state pages + core pages)
- **Dist folder:** `C:\WebAutomation\projects\inmate-lookup-site\dist\`
- **GitHub repo:** `cryptojuggernaut/jailinmate-net` (auto-deploys via Cloudflare Pages)

## What This Project Is
Directory site targeting inmate/court records search traffic.
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
- Google AdSense (after 2026-09-21)
- Bail bond affiliate program
- No database needed — pure static

## Remaining Tasks
- [x] Submit sitemap.xml to Google Search Console
- [x] Generate all 3,100 county pages
- [x] Push dist/ to GitHub + Cloudflare Pages
- [ ] Fix county pages — real sheriff URLs (replace all google.com/search links)
- [ ] Add unique content blocks per county (address, phone, hours)
- [ ] Add FAQ schema to every county page
- [ ] Set up Google Indexing API (console.cloud.google.com)
- [ ] Apply for bail bond affiliate program
- [ ] Apply for AdSense — NOT BEFORE 2026-09-21

## Workspace Rules
- Output to files only
- PowerShell syntax
- No clarifying questions


CEO — do NOT queue tasks mentioning: adsense, monetize, ad_setup, revenue milestones, ad units.
Full rejection analysis + fix plan: `projects/inmate-lookup-site/ADSENSE_REJECTION.md`

### Why it was rejected
The county pages are 95% identical template. Every "official" link is a `google.com/search?q=...`
URL — not a real `.gov` sheriff website. Google flagged this as thin/doorway pages.

### What to queue instead (content quality fixes):
1. **research** — Find real sheriff office URLs for top 20 US counties (see ADSENSE_REJECTION.md)
2. **web_dev** — Update `generate_pages.py` to use real URLs + county-specific address/phone data
3. **web_dev** — Regenerate + redeploy top 20 county pages with improved content

---

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

- 2026-07-10: competitor-intel plan #1 ran — report: `competitor_intel_2026-07-10.json` (8 steps)
