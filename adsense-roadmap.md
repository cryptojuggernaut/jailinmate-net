# jailinmate.net — AdSense Approval Roadmap

## Goal
Get jailinmate.net approved for AdSense by Sep 21, 2026 by ensuring all 3,100 county pages have AI-written content, are indexed by Google, and the site demonstrates consistent organic traffic.

## Tasks

- [ ] 1. Top up Anthropic API credits → Verify: `python -c "import anthropic; c=anthropic.Anthropic(); print(c.models.list())"` returns without 400 error
- [ ] 2. Regenerate all 3,100 county pages with AI content: `python generate_pages.py --all --force` → Verify: `python audit_pages.py` shows 3100/3100 pass and no `low_words` failures
- [ ] 3. Add `county_pages_gen` to SCE weekly scheduler so new/updated pages regenerate automatically: edit `sce/weekly_scheduler.py` to queue `county_pages_gen` task for `inmate-lookup-site` every Sunday → Verify: task appears in SCE queue on next Sunday
- [ ] 4. Set up Google Indexing API service account: create project at console.cloud.google.com, enable Indexing API, download JSON key to `sce/google_service_account.json`, add service account as GSC owner → Verify: `python sce/scripts/request_indexing.py --test` returns 200
- [ ] 5. Queue SCE `seo` task to request priority indexing for top 50 counties (by population): `curl -X POST http://localhost:8000/api/tasks -d '{"type":"seo","project":"inmate-lookup-site","payload":{"action":"request_indexing","priority_counties":50}}'` → Verify: task completes in SCE dashboard
- [ ] 6. Add weekly GSC monitoring to scheduler: queue `seo` task every Monday that fetches indexed page count from GSC API and logs to SCE DB → Verify: GSC indexed count appears in SCE project detail → SEO tab
- [ ] 7. Apply for AdSense on Sep 21, 2026: go to google.com/adsense/start, enter `https://jailinmate.net` → Verify: application submitted, confirmation email received

## Done When
- [ ] `python audit_pages.py` shows 3100/3100 with AI content (word count 800+, not template fallback)
- [ ] GSC Coverage report shows 2,000+ indexed pages
- [ ] AdSense application submitted by Sep 21, 2026

## Notes
- Tasks 1-2 are blockers — everything depends on API credits being available
- Task 4 (Indexing API) is the fastest path to getting pages indexed — don't skip it
- Template fallback pages (current state) pass SEO audit but have generic content; AI pages rank better
- County pages are in `dist/counties/` — sitemap now includes all 3,152 URLs
- SCE scheduler: `sce/weekly_scheduler.py` — add new entries following existing pattern
- AdSense minimum: domain age ~3 months (domain registered ~Mar 2026, eligible ~Jun 21, 2026 — may be eligible sooner than expected)
- Backlink strategy: submit site to legal/court resource directories; low effort, meaningful signal
