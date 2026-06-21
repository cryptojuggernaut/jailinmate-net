"""
Bulk SEO audit for all county pages in dist/counties/
Checks: OG tags, JSON-LD, H1, H2 count, word count, canonical,
        meta description, no dead links, no markdown fences, keywords.
"""
import re, sys
from pathlib import Path

DIST = Path(r"C:\WebAutomation\projects\inmate-lookup-site\dist\counties")
ISSUES = []

def word_count(html: str) -> int:
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&[a-z]+;', ' ', text)
    return len([w for w in text.split() if w])

def audit_file(path: Path) -> list:
    issues = []
    html = path.read_text(encoding="utf-8", errors="replace")

    if "```" in html:
        issues.append("markdown_fence")
    if 'href="#"' in html:
        issues.append("dead_link")
    if "<h1" not in html.lower():
        issues.append("missing_h1")
    if 'og:title' not in html:
        issues.append("missing_og_title")
    if 'og:description' not in html:
        issues.append("missing_og_description")
    if 'og:url' not in html:
        issues.append("missing_og_url")
    if 'application/ld+json' not in html:
        issues.append("missing_json_ld")
    if 'FAQPage' not in html:
        issues.append("missing_faq_schema")
    if 'rel="canonical"' not in html:
        issues.append("missing_canonical")
    if '<meta name="description"' not in html:
        issues.append("missing_meta_desc")

    h2_count = len(re.findall(r'<h2', html, re.IGNORECASE))
    if h2_count < 4:
        issues.append(f"low_h2:{h2_count}")

    wc = word_count(html)
    if wc < 600:
        issues.append(f"low_words:{wc}")

    # Keyword check — title should contain county + state
    slug = path.stem  # e.g. harris-county-texas-inmate-lookup
    parts = slug.replace("-inmate-lookup", "").split("-county-")
    if len(parts) == 2:
        county_kw = parts[0].replace("-", " ")
        state_kw = parts[1].replace("-", " ")
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).lower() if title_match else ""
        norm = lambda s: re.sub(r'[-\s]+', ' ', s).strip()
        if norm(county_kw) not in norm(title):
            issues.append(f"keyword_missing_county")
        if state_kw not in title:
            issues.append(f"keyword_missing_state")
        if "inmate" not in title:
            issues.append("keyword_missing_inmate")

    return issues

pages = sorted(DIST.glob("*.html"))
total = len(pages)
fail_list = []

print(f"Auditing {total} county pages...\n")

issue_counts = {}
for p in pages:
    issues = audit_file(p)
    if issues:
        fail_list.append((p.name, issues))
        for i in issues:
            key = i.split(":")[0]
            issue_counts[key] = issue_counts.get(key, 0) + 1

passed = total - len(fail_list)
print(f"PASSED: {passed}/{total}")
print(f"FAILED: {len(fail_list)}/{total}\n")

if issue_counts:
    print("Issue breakdown:")
    for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
        print(f"  {issue}: {count} pages")

if fail_list:
    out = Path(r"C:\WebAutomation\projects\inmate-lookup-site\audit_failures.txt")
    with open(out, "w", encoding="utf-8") as f:
        for name, issues in fail_list:
            f.write(f"{name}\t{','.join(issues)}\n")
    print(f"\nFailing pages written to: {out}")
else:
    print("\nAll pages pass! No failures.")
