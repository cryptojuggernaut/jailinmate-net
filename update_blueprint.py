"""Update site_plans blueprint_md to v2 for inmate-lookup-site."""
import sqlite3, datetime

BLUEPRINT = r"""# SITE BLUEPRINT v2: jailinmate.net

## Purpose
jailinmate.net is a free directory helping families find arrested loved ones across all U.S. county jails.
We provide county-specific search guides, official resource links, bail/visitation info, and FAQ pages.
We win by being faster to use, more complete, and better structured than government websites.

## Domain
https://jailinmate.net  (v1 blueprint used "FreeInmateLocator.com" — that name is retired)

## Target Audience
Family members of recently arrested individuals. Mobile-first (70%+). High anxiety, low familiarity
with the justice system. They need: WHERE is my loved one, HOW do I search, WHEN can I visit,
WHAT do I need to bring.

## URL Pattern
/counties/[county-slug]-county-[state-slug]-inmate-lookup.html
Example: /counties/los-angeles-county-california-inmate-lookup.html

---

## Page Template — MANDATORY elements on every page

### Head
- charset=UTF-8, viewport meta
- `<title>` = primary keyword (from keyword_map.json; fallback = "{County} County {State} Inmate Lookup")
- `<meta name="description">` 150–160 chars, includes primary keyword
- `<link rel="canonical" href="https://jailinmate.net/{slug}">` — REQUIRED
- Open Graph: og:type=article, og:title, og:description, og:url, og:site_name=jailinmate.net
- Twitter: summary card
- JSON-LD schema block — REQUIRED (see Schema section)
- AdSense: ca-pub-1410717606678785

### Navigation
- Top nav bar (#1a1a2e): Home · All States · About
- Breadcrumb: Home > {State} > {County} County

### Body — 7 H2 sections in this exact order
1. `<h1>{primary_keyword}</h1>` + 2–3 sentence intro (include keyword naturally)
2. `<h2>How to Search {County} County Jail Records</h2>` — `<ol>` 5 numbered steps
3. `<h2>Official {County} County Resources</h2>` — `<ul class="resource-list">` with real links:
   - County Sheriff inmate search (Google search URL — always works)
   - State DOC inmate locator (real state URL from state_doc_urls dict in generate_pages.py)
   - County court records (Google search URL)
   - Federal BOP locator (https://www.bop.gov/inmateloc/)
   - County bail bond info (Google search URL)
4. `<h2>Bail Bond Information for {County} County</h2>` — 2 paragraphs, 10% fee, arraignment timeline
5. `<h2>Visitation Rules at {County} County Jail</h2>` — `<ul>` with ID, hours, dress code, video visits, children
6. `<h2>What to Expect After Arrest in {County} County</h2>` — `<ol>` booking → medical → classification → arraignment → transfer
7. `<h2>How to Contact {County} County Jail</h2>` — paragraph + `<ul>` with 3 official links
8. `<h2>Frequently Asked Questions — {County} County Inmate Lookup</h2>` — 5 `<h3>` Q&A pairs

### Footer
Home · All States · {State} Counties · About · Privacy
© 2025 jailinmate.net — Links to official government sources only.

### Disclaimer box (.disclaimer)
Yellow background. States: not affiliated with any law enforcement, links to official sources only,
no personal information stored or sold.

---

## Schema Markup — REQUIRED on every page

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "FAQPage",
      "mainEntity": [
        {"@type": "Question", "name": "...", "acceptedAnswer": {"@type": "Answer", "text": "..."}}
      ]
    },
    {
      "@type": "WebPage",
      "name": "{primary_keyword}",
      "description": "{meta description}",
      "url": "https://jailinmate.net/{slug}",
      "publisher": {"@type": "Organization", "name": "jailinmate.net", "url": "https://jailinmate.net"}
    }
  ]
}
```

---

## Quality Rules — NEVER Violate

### Absolutely forbidden in any generated page
- `href="#"` — every link must be a real URL
- Markdown artifacts: no backtick fences, no **bold**, no # headings as text
- Missing `<h1>` tag
- Body content under 1200 characters
- Missing canonical tag
- Missing JSON-LD schema block
- Character encoding bugs — always write UTF-8, use real Unicode (—, →, etc.)
- Pages from the old generator (built before 2026-06-14) have all of these issues
  and must be regenerated with `python generate_pages.py --all --force`

### Required in every page
- Canonical link pointing to https://jailinmate.net/...
- FAQPage + WebPage JSON-LD schema
- Real external links (no internal-only pages)
- Breadcrumb nav
- Disclaimer box
- 800–900 words in the body

---

## Validation Gate (enforced in generate_pages.py — added 2026-06-14)

`_validate_body()` is called on every AI response before it is accepted.
It rejects (falls back to template) if any of these fail:
1. No HTML tags found — catches raw text / markdown output
2. Markdown fence (```) present
3. `href="#"` dead link present
4. `<h1>` missing
5. Fewer than 4 of 7 required H2 sections found
6. No external http link
7. Body < 1200 characters
8. Starts with "html" (fence artifact)

`run()` also checks the final assembled HTML before writing to disk:
- Missing `rel="canonical"` → SKIP
- Missing `application/ld+json` → SKIP

Failures fall back to `_template_fallback()` which always passes all checks.

---

## Scale
- 3,176 county pages built to date in dist/counties/
- Target: all 3,143 US counties (one page each)
- Pages built before 2026-06-14 used the old generator and need `--force` regeneration

## Keyword Strategy
Primary keyword per county comes from keyword_data/keyword_map.json (run keyword_agent.py first).
Fallback: "{County} County {State} Inmate Lookup"

## Internal Linking
- County page → /states/{state_abbr}.html (state index)
- Nav → /states.html (all states)
- Footer → Home, All States, State, About, Privacy
- No orphan pages

## Files
| File | Purpose |
|------|---------|
| generate_pages.py | Generator — keyword lookup, Claude Haiku, template, validate, write |
| keyword_agent.py | Keyword researcher — populates keyword_data/keyword_map.json |
| fix_state_pages.py | State index page builder |
| dist/counties/ | 3,000+ county HTML pages |

## Deployment
Cloudflare Pages → jailinmate.net
AdSense publisher: ca-pub-1410717606678785
"""

now = datetime.datetime.utcnow().isoformat()
conn = sqlite3.connect(r"C:\WebAutomation\sce\db\sce.db")
conn.execute(
    """UPDATE site_plans
       SET blueprint_md=?, version=2, status='approved',
           blueprint_at=?, approved_at=?, updated_at=?
       WHERE project='inmate-lookup-site'""",
    (BLUEPRINT, now, now, now),
)
conn.commit()
row = conn.execute(
    "SELECT id, project, version, status, length(blueprint_md) as bp_len FROM site_plans WHERE project='inmate-lookup-site'"
).fetchone()
print(f"Updated: id={row[0]} project={row[1]} version={row[2]} status={row[3]} blueprint_length={row[4]}")
conn.close()
