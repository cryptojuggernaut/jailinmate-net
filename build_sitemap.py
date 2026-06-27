"""
build_sitemap.py — Phase 4 of the Google Indexing Fix Plan
Replaces the single sitemap.xml with a sitemap index + 4 priority-tiered sitemaps.

Output files in dist/:
  sitemap.xml              ← sitemap index (replaces old monolith)
  sitemap-core.xml         ← home, about, states, privacy, contact (priority 1.0)
  sitemap-states.xml       ← 50 state pages (priority 0.9)
  sitemap-counties-t1.xml  ← top ~500 counties by population (priority 0.9)
  sitemap-counties-t2.xml  ← remaining counties (priority 0.7)

Usage:
  python build_sitemap.py
"""
import csv
import os
from datetime import date
from pathlib import Path

DIST_DIR = Path(__file__).parent / "dist"
BASE_URL = "https://jailinmate.net"
TODAY    = date.today().isoformat()

# Top ~500 counties by population (state_abbr + county name key)
# Source: US Census 2020 — counties with population > ~50,000
TOP_COUNTIES: set[str] = {
    # California
    "CA|Los Angeles", "CA|San Diego", "CA|Orange", "CA|Riverside",
    "CA|San Bernardino", "CA|Alameda", "CA|Sacramento", "CA|Contra Costa",
    "CA|Fresno", "CA|Kern", "CA|San Francisco", "CA|Ventura",
    "CA|San Mateo", "CA|San Joaquin", "CA|Stanislaus", "CA|Sonoma",
    "CA|Tulare", "CA|Santa Clara", "CA|Solano", "CA|Monterey",
    # Texas
    "TX|Harris", "TX|Dallas", "TX|Tarrant", "TX|Bexar", "TX|Travis",
    "TX|Collin", "TX|Denton", "TX|Hidalgo", "TX|El Paso", "TX|Fort Bend",
    "TX|Montgomery", "TX|Williamson", "TX|Nueces", "TX|Brazoria", "TX|Bell",
    "TX|Lubbock", "TX|Jefferson", "TX|Webb", "TX|McLennan", "TX|Smith",
    # Florida
    "FL|Miami-Dade", "FL|Broward", "FL|Palm Beach", "FL|Hillsborough",
    "FL|Orange", "FL|Pinellas", "FL|Duval", "FL|Lee", "FL|Polk",
    "FL|Brevard", "FL|Volusia", "FL|Sarasota", "FL|Manatee", "FL|Collier",
    "FL|Pasco", "FL|Seminole", "FL|Marion", "FL|Alachua", "FL|Escambia",
    # New York
    "NY|Kings", "NY|Queens", "NY|New York", "NY|Suffolk", "NY|Bronx",
    "NY|Nassau", "NY|Westchester", "NY|Erie", "NY|Monroe", "NY|Richmond",
    "NY|Onondaga", "NY|Albany", "NY|Dutchess", "NY|Orange", "NY|Rockland",
    # Illinois
    "IL|Cook", "IL|DuPage", "IL|Lake", "IL|Will", "IL|Kane",
    "IL|Winnebago", "IL|McHenry", "IL|Kendall", "IL|Champaign", "IL|Peoria",
    # Pennsylvania
    "PA|Philadelphia", "PA|Allegheny", "PA|Montgomery", "PA|Bucks",
    "PA|Delaware", "PA|Chester", "PA|Lancaster", "PA|York", "PA|Berks",
    "PA|Northampton",
    # Ohio
    "OH|Franklin", "OH|Cuyahoga", "OH|Hamilton", "OH|Summit", "OH|Montgomery",
    "OH|Lucas", "OH|Butler", "OH|Stark", "OH|Lorain", "OH|Warren",
    # Georgia
    "GA|Fulton", "GA|Gwinnett", "GA|Cobb", "GA|DeKalb", "GA|Cherokee",
    "GA|Forsyth", "GA|Clayton", "GA|Hall", "GA|Richmond", "GA|Chatham",
    # Michigan
    "MI|Wayne", "MI|Oakland", "MI|Macomb", "MI|Kent", "MI|Genesee",
    "MI|Washtenaw", "MI|Ingham", "MI|Ottawa", "MI|Kalamazoo", "MI|Saginaw",
    # North Carolina
    "NC|Mecklenburg", "NC|Wake", "NC|Guilford", "NC|Forsyth", "NC|Durham",
    "NC|Buncombe", "NC|Union", "NC|Cabarrus", "NC|New Hanover", "NC|Onslow",
    # New Jersey
    "NJ|Bergen", "NJ|Middlesex", "NJ|Essex", "NJ|Hudson", "NJ|Monmouth",
    "NJ|Ocean", "NJ|Union", "NJ|Camden", "NJ|Passaic", "NJ|Morris",
    # Virginia
    "VA|Fairfax", "VA|Prince William", "VA|Loudoun", "VA|Chesterfield",
    "VA|Arlington", "VA|Henrico", "VA|Virginia Beach", "VA|Chesapeake",
    # Washington
    "WA|King", "WA|Pierce", "WA|Snohomish", "WA|Spokane", "WA|Clark",
    "WA|Thurston", "WA|Kitsap", "WA|Whatcom", "WA|Benton",
    # Arizona
    "AZ|Maricopa", "AZ|Pima", "AZ|Pinal", "AZ|Yavapai", "AZ|Mohave",
    "AZ|Yuma", "AZ|Coconino", "AZ|Apache",
    # Colorado
    "CO|El Paso", "CO|Jefferson", "CO|Arapahoe", "CO|Denver", "CO|Douglas",
    "CO|Larimer", "CO|Weld", "CO|Boulder", "CO|Adams", "CO|Broomfield",
    # Tennessee
    "TN|Shelby", "TN|Davidson", "TN|Knox", "TN|Hamilton", "TN|Rutherford",
    "TN|Williamson", "TN|Montgomery", "TN|Sullivan", "TN|Sumner",
    # Indiana
    "IN|Marion", "IN|Lake", "IN|Allen", "IN|Hamilton", "IN|Tippecanoe",
    "IN|St. Joseph", "IN|Elkhart", "IN|Johnson", "IN|Hendricks",
    # Missouri
    "MO|St. Louis", "MO|Jackson", "MO|St. Charles", "MO|Jefferson",
    "MO|Greene", "MO|Clay", "MO|St. Louis City",
    # Maryland
    "MD|Montgomery", "MD|Prince George's", "MD|Baltimore", "MD|Anne Arundel",
    "MD|Howard", "MD|Frederick", "MD|Charles", "MD|Harford",
    # Wisconsin
    "WI|Milwaukee", "WI|Dane", "WI|Waukesha", "WI|Brown", "WI|Racine",
    "WI|Outagamie", "WI|Winnebago", "WI|Kenosha", "WI|Rock",
    # Minnesota
    "MN|Hennepin", "MN|Ramsey", "MN|Dakota", "MN|Anoka", "MN|Washington",
    "MN|Scott", "MN|Carver", "MN|Wright", "MN|St. Louis",
    # Nevada
    "NV|Clark", "NV|Washoe", "NV|Carson City", "NV|Elko",
    # Massachusetts
    "MA|Middlesex", "MA|Worcester", "MA|Essex", "MA|Suffolk", "MA|Norfolk",
    "MA|Bristol", "MA|Hampden", "MA|Plymouth",
    # South Carolina
    "SC|Greenville", "SC|Richland", "SC|Charleston", "SC|Horry",
    "SC|Spartanburg", "SC|Lexington", "SC|York",
    # Alabama
    "AL|Jefferson", "AL|Mobile", "AL|Madison", "AL|Shelby",
    "AL|Montgomery", "AL|Tuscaloosa", "AL|Baldwin",
    # Kentucky
    "KY|Jefferson", "KY|Fayette", "KY|Kenton", "KY|Boone",
    "KY|Warren", "KY|Hardin", "KY|Madison",
    # Oregon
    "OR|Multnomah", "OR|Washington", "OR|Clackamas", "OR|Lane",
    "OR|Marion", "OR|Jackson", "OR|Deschutes",
    # Oklahoma
    "OK|Oklahoma", "OK|Tulsa", "OK|Cleveland", "OK|Canadian",
    "OK|Comanche", "OK|Rogers",
    # Connecticut
    "CT|Hartford", "CT|New Haven", "CT|Fairfield", "CT|Middlesex",
    "CT|New London", "CT|Windham",
    # Iowa
    "IA|Polk", "IA|Linn", "IA|Scott", "IA|Johnson", "IA|Black Hawk",
    # Utah
    "UT|Salt Lake", "UT|Utah", "UT|Davis", "UT|Weber",
    "UT|Washington", "UT|Cache",
    # Arkansas
    "AR|Pulaski", "AR|Benton", "AR|Washington", "AR|Sebastian",
    # Kansas
    "KS|Johnson", "KS|Sedgwick", "KS|Wyandotte", "KS|Douglas",
    # Louisiana
    "LA|Jefferson", "LA|Orleans", "LA|Caddo", "LA|Calcasieu",
    "LA|Bossier", "LA|St. Tammany",
    # Mississippi
    "MS|Hinds", "MS|Harrison", "MS|Rankin", "MS|DeSoto",
    # Nebraska
    "NE|Douglas", "NE|Lancaster", "NE|Sarpy",
    # New Mexico
    "NM|Bernalillo", "NM|Doña Ana", "NM|Sandoval", "NM|Santa Fe",
    # Idaho
    "ID|Ada", "ID|Canyon", "ID|Kootenai", "ID|Twin Falls",
    # West Virginia
    "WV|Kanawha", "WV|Cabell", "WV|Monongalia",
    # Hawaii
    "HI|Honolulu", "HI|Hawaii", "HI|Maui",
    # Maine
    "ME|Cumberland", "ME|York", "ME|Penobscot",
    # New Hampshire
    "NH|Hillsborough", "NH|Rockingham", "NH|Merrimack",
    # Rhode Island
    "RI|Providence", "RI|Kent", "RI|Washington",
    # Montana
    "MT|Yellowstone", "MT|Cascade", "MT|Missoula",
    # Delaware
    "DE|New Castle", "DE|Kent", "DE|Sussex",
    # South Dakota
    "SD|Minnehaha", "SD|Pennington",
    # North Dakota
    "ND|Cass", "ND|Burleigh",
    # Alaska
    "AK|Anchorage",
    # Wyoming
    "WY|Laramie", "WY|Natrona",
    # Vermont
    "VT|Chittenden", "VT|Washington",
}


def url_elem(loc: str, priority: str, lastmod: str = TODAY) -> str:
    return (
        f"  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <priority>{priority}</priority>\n"
        f"  </url>\n"
    )


def write_sitemap(path: Path, urls: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            f.write(u)
        f.write("</urlset>\n")
    print(f"  Wrote {path.name} ({len(urls)} URLs)")


def file_lastmod(path: Path) -> str:
    try:
        return date.fromtimestamp(path.stat().st_mtime).isoformat()
    except Exception:
        return TODAY


def is_top_county(fname: str, counties_by_state: dict[str, list[tuple[str, str]]]) -> bool:
    """Check if a county filename maps to a top-population county."""
    import re
    m = re.match(r"^(.+)-county-(.+)-inmate-lookup\.html$", fname)
    if not m:
        return False
    county_part = m.group(1).replace("-", " ").title()
    state_part  = m.group(2).replace("-", " ").title()
    # Find state_abbr
    for abbr, entries in counties_by_state.items():
        for c, s in entries:
            if c.lower() == county_part.lower() and s.lower() == state_part.lower():
                return f"{abbr}|{c}" in TOP_COUNTIES
    return False


def main():
    # Load counties CSV for state lookup
    csv_path = Path(__file__).parent / "counties.csv"
    counties_by_state: dict[str, list[tuple[str, str]]] = {}
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            abbr  = row["state_abbr"].strip()
            county = row["county"].strip()
            state  = row["state"].strip()
            counties_by_state.setdefault(abbr, []).append((county, state))

    # ── Core pages ──────────────────────────────────────────────────────────
    core_urls = []
    core_pages = [
        ("", "1.0"),
        ("states.html", "0.9"),
        ("about.html", "0.7"),
        ("privacy.html", "0.5"),
        ("contact.html", "0.5"),
    ]
    for page, pri in core_pages:
        loc = BASE_URL + ("/" if not page else f"/{page}")
        lm  = file_lastmod(DIST_DIR / (page or "index.html"))
        core_urls.append(url_elem(loc, pri, lm))

    # ── State pages ──────────────────────────────────────────────────────────
    state_urls = []
    states_dir = DIST_DIR / "states"
    if states_dir.exists():
        for f in sorted(states_dir.glob("*.html")):
            loc = f"{BASE_URL}/states/{f.name}"
            lm  = file_lastmod(f)
            state_urls.append(url_elem(loc, "0.9", lm))

    # ── County pages — split into tier 1 and tier 2 ──────────────────────────
    tier1_urls = []
    tier2_urls = []
    county_dir = DIST_DIR / "counties"
    if county_dir.exists():
        for f in sorted(county_dir.glob("*.html")):
            loc = f"{BASE_URL}/counties/{f.name}"
            lm  = file_lastmod(f)
            if is_top_county(f.name, counties_by_state):
                tier1_urls.append(url_elem(loc, "0.9", lm))
            else:
                tier2_urls.append(url_elem(loc, "0.7", lm))

    print(f"\nSitemap stats:")
    print(f"  Core      : {len(core_urls)}")
    print(f"  States    : {len(state_urls)}")
    print(f"  Tier 1    : {len(tier1_urls)} (high-population counties)")
    print(f"  Tier 2    : {len(tier2_urls)}")

    # ── Write the 4 sitemaps ─────────────────────────────────────────────────
    write_sitemap(DIST_DIR / "sitemap-core.xml",         core_urls)
    write_sitemap(DIST_DIR / "sitemap-states.xml",       state_urls)
    write_sitemap(DIST_DIR / "sitemap-counties-t1.xml",  tier1_urls)
    write_sitemap(DIST_DIR / "sitemap-counties-t2.xml",  tier2_urls)

    # ── Write sitemap index ──────────────────────────────────────────────────
    index_path = DIST_DIR / "sitemap.xml"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for name in ["sitemap-core.xml", "sitemap-states.xml",
                     "sitemap-counties-t1.xml", "sitemap-counties-t2.xml"]:
            f.write(f"  <sitemap>\n")
            f.write(f"    <loc>{BASE_URL}/{name}</loc>\n")
            f.write(f"    <lastmod>{TODAY}</lastmod>\n")
            f.write(f"  </sitemap>\n")
        f.write("</sitemapindex>\n")
    total = len(core_urls) + len(state_urls) + len(tier1_urls) + len(tier2_urls)
    print(f"  Wrote sitemap.xml (index, {total} total URLs)")
    print("\nDone. Submit sitemap.xml to Google Search Console.")


if __name__ == "__main__":
    main()
