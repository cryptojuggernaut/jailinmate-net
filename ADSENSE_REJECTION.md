# AdSense Rejection — Root Cause & Fix Plan

**Status:** BLOCKED until content quality fixes are complete.
**Date:** 2026-06-29
**Rejection reason:** Low value content / thin content

---

## Why Google Rejected It

Every county page is ~95% identical template with only the county name swapped in:

1. **"Official Resources" links are Google Search URLs** — not real sheriff/court websites
   ```
   https://www.google.com/search?q=cook-county-il-sheriff-inmate-search
   ```
   Google sees pages that link back to Google. This looks like a doorway page farm.

2. **5 FAQs are word-for-word identical** across 3,152 pages — only `{county}` changes
3. **No unique local data** — no real jail address, phone, capacity, booking hours, or staff
4. **No real external links** to actual government domains (`.gov`, `.us`)
5. **3,152 pages × 95% duplicate = classic thin content at scale**

Google's quality threshold: each page must be **meaningfully different** and provide **genuine user value** that couldn't be found anywhere else on the site.

---

## What Needs to Change (in order)

### Phase 1 — Real Sheriff URLs (highest impact)
Replace the Google Search fallback links with actual sheriff office URLs.

**Data needed:** CSV with columns: `county, state, state_abbr, sheriff_url, jail_address, jail_phone`

Sources:
- `https://www.naco.org/resources/sheriff-offices` — National Association of Counties
- State-specific sheriff association directories
- Manual research for top 100 counties by population

**Minimum viable:** Just replace `sheriff_url` — even a real `.gov` or `.us` link changes the quality signal dramatically.

### Phase 2 — Per-County Unique Data Block
Add a county-specific data section at the top of each page:

```html
<div class="county-info-card">
  <h2>Cook County Jail — Quick Facts</h2>
  <ul>
    <li><strong>Address:</strong> 2700 S California Ave, Chicago, IL 60608</li>
    <li><strong>Phone:</strong> (773) 674-7000</li>
    <li><strong>Capacity:</strong> ~7,500 inmates</li>
    <li><strong>Online search:</strong> <a href="https://www2.cookcountysheriff.org/search2/">Official Inmate Search</a></li>
    <li><strong>Booking hours:</strong> 24/7</li>
    <li><strong>Video visitation:</strong> Via Cisco (must schedule 24hr in advance)</li>
  </ul>
</div>
```

**Data needed:** For top 500 counties — address, phone, real search URL, capacity, video visit system

### Phase 3 — Differentiated FAQ Content
Instead of the same 5 questions on every page, make 2-3 questions county-specific:
- "What is the Cook County Department of Corrections phone number?" → real answer
- "Where is the Cook County Jail located?" → real address
- "How many people are held in Cook County Jail?" → real capacity

### Phase 4 — Remove Google Search Links Entirely
The fallback links that go to `google.com/search?q=...` must be replaced or removed.
Google penalizes pages that exist only to send traffic back to Google.

---

## Data Acquisition Strategy

### Option A — Automated scraping (fast, free)
```python
# Scrape NACO county directory for sheriff URLs
# Scrape each state's sheriff association for contact info
# ~2-3 days of scraping with rate limiting
```

### Option B — OpenData sources (clean, no scraping needed)
- USAFacts.org county data
- data.gov government directory datasets  
- Each state's open data portal

### Option C — AI-assisted research (slowest, most complete)
- For each of top 500 counties, use web search to find real URLs
- Queue as `research` tasks in SCE — one county at a time
- ~500 research tasks × $0.01 each = ~$5 of API cost

**Recommended:** Option A (scraping NACO) + Option B (supplement with open data) for the top 500 counties, then expand.

---

## Files to Modify

| File | Change |
|------|--------|
| `generate_pages.py` | Add real_data dict per county; replace Google search fallbacks with real URLs |
| `generate_pages.py` | Add county-specific data card HTML block |
| `generate_pages.py` | Make 2-3 FAQs use real county data (address, phone) |
| New: `county_data.json` | County-level data: address, phone, url, capacity |
| New: `scrape_sheriff_data.py` | One-time scraper to build county_data.json |

---

## Success Criteria Before Reapplying to AdSense

- [ ] Top 100 county pages each have a real sheriff URL (no google.com/search links)
- [ ] Top 100 county pages each have a real jail address and phone number
- [ ] FAQ section has at least 2 county-specific questions with real answers
- [ ] No two pages have more than 70% identical text content
- [ ] Site has been live for 90+ days with consistent traffic (Shane to confirm timing)
- [ ] Shane explicitly says "apply for AdSense"

---

## CEO Instructions (read by ceo_agent on next run)

**DO NOT queue any of these task types until Shane says AdSense is ready:**
- adsense, monetize, revenue, ad_setup, ad_integration

**DO queue these content quality tasks:**
- `research` — find real sheriff URLs for top 50 counties
- `web_dev` — implement county_data.json + update generate_pages.py  
- `content` — regenerate top 100 county pages with real data after data is built

**Priority order:**
1. Build `county_data.json` with real URLs for top 100 counties
2. Update `generate_pages.py` to use it
3. Regenerate + redeploy top 100 pages
4. Monitor GSC for quality improvement signal (4-8 weeks)
5. Wait for Shane's go-ahead on AdSense
