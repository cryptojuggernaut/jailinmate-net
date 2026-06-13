"""
keyword_agent.py — Self-Learning Keyword Research Agent for jailinmate.net
C:\\WebAutomation\\projects\\inmate-lookup-site\\keyword_agent.py

Architecture:
  1. RESEARCH  — Pull keyword suggestions from Google Autocomplete (free, no API)
  2. SCORE     — Rank candidates by search intent, specificity, competition signals
  3. SELECT    — Pick the best primary keyword per county page
  4. LEARN     — After deploy, check real DuckDuckGo rankings weekly
  5. IMPROVE   — Use ranking history to refine which keyword patterns win
  6. REWRITE   — Re-optimise pages sitting at rank 11-30 with a better pattern

Self-learning loop:
  - Tracks every keyword variant tried and its eventual rank
  - Builds a pattern model: "[county] jail roster" vs "[county] inmate lookup" etc.
  - Routes new counties to whichever pattern currently has the best median rank
  - Auto-reoptimises underperforming pages every 30 days

Usage:
  python keyword_agent.py --county "Cook" --state "Illinois" --state-abbr IL
  python keyword_agent.py --all-counties              # research whole CSV
  python keyword_agent.py --rank-check                # weekly rank update
  python keyword_agent.py --reoptimise                # rewrite rank 11-30 pages
  python keyword_agent.py --report                    # print pattern leaderboard
"""

import os, sys, json, time, csv, re, sqlite3, argparse, html as _html
import urllib.request, urllib.parse
import ssl
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
DIST_DIR    = PROJECT_DIR / "dist"
DATA_DIR    = PROJECT_DIR / "keyword_data"
DB_PATH     = DATA_DIR / "keywords.db"
CSV_PATH    = PROJECT_DIR / "counties.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Keyword patterns we test. {c}=county, {s}=state ──────────────────────────
PATTERNS = [
    "{c} County {s} inmate lookup",
    "{c} County {s} jail roster",
    "{c} County {s} jail inmate search",
    "{c} County {s} inmate search",
    "{c} County {s} arrest records",
    "{c} County {s} jail records",
    "{c} {s} inmate locator",
    "{c} County {s} who's in jail",
    "{c} County jail roster {s}",
    "{c} County {s} detention center inmate search",
]

DOMAIN = "jailinmate.net"


# ── Database ───────────────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS keywords (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            county      TEXT NOT NULL,
            state       TEXT NOT NULL,
            state_abbr  TEXT NOT NULL,
            keyword     TEXT NOT NULL,
            pattern_id  INTEGER,          -- index into PATTERNS list
            source      TEXT DEFAULT 'generated',  -- generated | autocomplete | pai
            score       REAL DEFAULT 0,
            selected    INTEGER DEFAULT 0, -- 1 = this was chosen for the page
            rank        INTEGER,           -- last DuckDuckGo rank (NULL = not checked)
            rank_checked_at TEXT,
            rank_history    TEXT DEFAULT '[]', -- JSON list of {rank, checked_at}
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pattern_performance (
            pattern_id  INTEGER PRIMARY KEY,
            pattern     TEXT NOT NULL,
            n_pages     INTEGER DEFAULT 0,   -- pages using this pattern
            n_ranked    INTEGER DEFAULT 0,   -- pages with rank <= 100
            median_rank REAL,
            top10_count INTEGER DEFAULT 0,
            top30_count INTEGER DEFAULT 0,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS page_optimisation_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            county      TEXT NOT NULL,
            state       TEXT NOT NULL,
            old_keyword TEXT,
            new_keyword TEXT,
            old_rank    INTEGER,
            action      TEXT,   -- rewrite | skip | pending
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_kw_county ON keywords(county, state);
        CREATE INDEX IF NOT EXISTS idx_kw_selected ON keywords(selected);
        """)
    print("[db] Initialised keyword database")


# ── Google Autocomplete (free, no API key) ────────────────────────────────────

def google_autocomplete(query: str, retries: int = 2) -> list[str]:
    """
    Pull autocomplete suggestions from Google's public suggest endpoint.
    Returns list of suggestion strings.
    """
    suggestions = []
    encoded = urllib.parse.quote(query)
    url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={encoded}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124",
        "Accept-Language": "en-US,en;q=0.9",
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
                suggestions = data[1] if len(data) > 1 else []
                break
        except Exception as e:
            if attempt == retries:
                print(f"  [autocomplete] failed for '{query}': {e}")
    return suggestions


def gather_autocomplete_keywords(county: str, state: str) -> list[dict]:
    """
    Run multiple seed queries and collect all autocomplete suggestions.
    Returns [{keyword, source, score}]
    """
    seeds = [
        f"{county} County {state} inmate",
        f"{county} County {state} jail",
        f"{county} County {state} arrest",
        f"{county} jail roster",
        f"{county} County inmate search",
    ]
    seen = set()
    results = []
    for seed in seeds:
        suggestions = google_autocomplete(seed)
        for sug in suggestions:
            sug = sug.strip().lower()
            if sug and sug not in seen and len(sug) > 10:
                seen.add(sug)
                results.append({
                    "keyword": sug,
                    "source": "autocomplete",
                    "score": 0,
                })
        time.sleep(0.4)  # polite delay
    return results


# ── Keyword scoring ────────────────────────────────────────────────────────────

POSITIVE_SIGNALS = [
    "inmate lookup", "inmate search", "jail roster", "jail records",
    "arrest records", "who's in jail", "inmate locator", "detention",
    "mugshot", "booking", "county jail",
]
NEGATIVE_SIGNALS = [
    "death row", "federal", "sex offender", "wikipedia", "how to become",
    "salary", "officer", "commissioner",
]

def score_keyword(keyword: str, county: str, state: str) -> float:
    """
    Score a keyword 0-100 based on signals likely to indicate search intent
    and ranking opportunity.
    """
    kw = keyword.lower()
    score = 50.0

    # County + state specificity bonus
    county_lower = county.lower()
    state_lower  = state.lower()
    if county_lower in kw:
        score += 15
    if state_lower in kw or state_lower[:4] in kw:
        score += 8

    # Intent signals
    for sig in POSITIVE_SIGNALS:
        if sig in kw:
            score += 12
            break

    # Negative signals
    for sig in NEGATIVE_SIGNALS:
        if sig in kw:
            score -= 30

    # Length penalty (too short = too broad, too long = low volume)
    words = kw.split()
    if len(words) < 3:
        score -= 20
    elif len(words) > 8:
        score -= 10

    # "Free" modifier bonus — high intent
    if "free" in kw:
        score += 8

    return max(0.0, min(100.0, score))


def score_all(candidates: list[dict], county: str, state: str) -> list[dict]:
    for c in candidates:
        c["score"] = score_keyword(c["keyword"], county, state)
    return sorted(candidates, key=lambda x: x["score"], reverse=True)


# ── Pattern model (self-learning) ─────────────────────────────────────────────

def get_best_pattern(conn: sqlite3.Connection) -> int:
    """
    Return the pattern_id that currently has the best median rank.
    Falls back to pattern 0 if no data yet.
    """
    rows = conn.execute("""
        SELECT pattern_id, median_rank, n_ranked
        FROM pattern_performance
        WHERE n_ranked >= 3
        ORDER BY median_rank ASC
        LIMIT 1
    """).fetchone()
    return rows["pattern_id"] if rows else 0


def build_pattern_keywords(county: str, state: str) -> list[dict]:
    """Generate one candidate keyword per pattern."""
    return [
        {
            "keyword": p.format(c=county, s=state),
            "pattern_id": i,
            "source": "generated",
            "score": 0,
        }
        for i, p in enumerate(PATTERNS)
    ]


def update_pattern_performance(conn: sqlite3.Connection):
    """Recompute pattern performance stats from keyword ranking history."""
    for i, pattern in enumerate(PATTERNS):
        rows = conn.execute("""
            SELECT rank FROM keywords
            WHERE pattern_id = ? AND selected = 1 AND rank IS NOT NULL
        """, (i,)).fetchall()
        ranks = [r["rank"] for r in rows]
        if not ranks:
            conn.execute("""
                INSERT OR REPLACE INTO pattern_performance
                (pattern_id, pattern, n_pages, n_ranked, median_rank, top10_count, top30_count, updated_at)
                VALUES (?, ?, ?, 0, NULL, 0, 0, datetime('now'))
            """, (i, pattern, 0))
            continue

        sorted_ranks = sorted(ranks)
        n = len(sorted_ranks)
        median = sorted_ranks[n // 2] if n % 2 else (sorted_ranks[n//2-1] + sorted_ranks[n//2]) / 2
        top10  = sum(1 for r in ranks if r <= 10)
        top30  = sum(1 for r in ranks if r <= 30)
        n_pages = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE pattern_id = ? AND selected = 1", (i,)
        ).fetchone()[0]

        conn.execute("""
            INSERT OR REPLACE INTO pattern_performance
            (pattern_id, pattern, n_pages, n_ranked, median_rank, top10_count, top30_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (i, pattern, n_pages, n, median, top10, top30))
    conn.commit()


# ── Main research flow ────────────────────────────────────────────────────────

def research_county(county: str, state: str, state_abbr: str,
                    use_autocomplete: bool = True) -> dict:
    """
    Full keyword research for one county.
    Returns the selected best keyword and all candidates.
    """
    print(f"\n[research] {county} County, {state}")

    with get_conn() as conn:
        # Check if already researched
        existing = conn.execute(
            "SELECT keyword FROM keywords WHERE county=? AND state=? AND selected=1",
            (county, state)
        ).fetchone()
        if existing:
            print(f"  [skip] already have selected keyword: {existing['keyword']}")
            return {"county": county, "state": state, "keyword": existing["keyword"], "skipped": True}

        # 1. Generate pattern-based candidates
        candidates = build_pattern_keywords(county, state)

        # 2. Pull autocomplete suggestions (live Google data)
        if use_autocomplete:
            ac = gather_autocomplete_keywords(county, state)
            candidates.extend(ac)

        # 3. Score all candidates
        candidates = score_all(candidates, county, state)

        # 4. Pick winner — prefer the best-performing pattern if we have data,
        #    else pick the highest-scoring candidate overall
        best_pattern_id = get_best_pattern(conn)
        pattern_candidate = next(
            (c for c in candidates if c.get("pattern_id") == best_pattern_id),
            None
        )
        # Also pick the highest-scoring overall
        top_scored = candidates[0] if candidates else None

        # Use pattern winner if its score is within 15pts of top_scored, else use top_scored
        if pattern_candidate and top_scored:
            if top_scored["score"] - pattern_candidate["score"] <= 15:
                winner = pattern_candidate
            else:
                winner = top_scored
        else:
            winner = top_scored or {"keyword": f"{county} County {state} inmate lookup",
                                    "pattern_id": 0, "source": "fallback", "score": 50}

        # 5. Store all candidates
        for c in candidates[:30]:  # top 30
            conn.execute("""
                INSERT INTO keywords
                (county, state, state_abbr, keyword, pattern_id, source, score, selected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                county, state, state_abbr,
                c["keyword"],
                c.get("pattern_id"),
                c.get("source", "autocomplete"),
                c["score"],
                1 if c["keyword"] == winner["keyword"] else 0,
            ))
        conn.commit()

    print(f"  [OK] Selected: \"{winner['keyword']}\" (score={winner['score']:.0f})")
    return {
        "county": county,
        "state": state,
        "state_abbr": state_abbr,
        "keyword": winner["keyword"],
        "score": winner["score"],
        "pattern_id": winner.get("pattern_id"),
    }


# ── Rank checking (self-learning feedback loop) ────────────────────────────────

def check_rank(keyword: str, domain: str = DOMAIN) -> Optional[int]:
    """Check DuckDuckGo rank. Returns position (1-based) or None."""
    try:
        query = urllib.parse.quote(keyword)
        url   = f"https://html.duckduckgo.com/html/?q={query}"
        ctx   = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            body = r.read().decode("utf-8", errors="replace")

        links = re.findall(r'class="result__url"[^>]*>([^<]+)<', body)
        if not links:
            links = re.findall(r'href="//duckduckgo\.com/l/\?[^"]*uddg=([^"&]+)', body)
            links = [urllib.parse.unquote(l) for l in links]

        domain_lower = domain.lower().replace("www.", "")
        for i, link in enumerate(links[:100], 1):
            if domain_lower in _html.unescape(link).lower():
                return i
    except Exception as e:
        print(f"  [rank check error] {keyword}: {e}")
    return None


def run_rank_checks(limit: int = 50):
    """
    Check rankings for selected keywords, oldest-checked first.
    Updates pattern performance after.
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, county, state, keyword
            FROM keywords
            WHERE selected = 1
            ORDER BY rank_checked_at ASC NULLS FIRST
            LIMIT ?
        """, (limit,)).fetchall()

        print(f"\n[rank-check] Checking {len(rows)} keywords against DuckDuckGo…")
        for row in rows:
            rank = check_rank(row["keyword"])
            now  = datetime.now(timezone.utc).isoformat()

            # Append to history
            history_raw = conn.execute(
                "SELECT rank_history FROM keywords WHERE id=?", (row["id"],)
            ).fetchone()["rank_history"] or "[]"
            history = json.loads(history_raw)
            history.append({"rank": rank, "checked_at": now})
            history = history[-12:]  # keep last 12 snapshots (~3 months weekly)

            conn.execute("""
                UPDATE keywords
                SET rank=?, rank_checked_at=?, rank_history=?, updated_at=?
                WHERE id=?
            """, (rank, now, json.dumps(history), now, row["id"]))

            rank_str = f"#{rank}" if rank else "not found"
            print(f"  {row['county']}, {row['state']}: \"{row['keyword']}\" → {rank_str}")
            time.sleep(2.0)  # polite delay between requests

        conn.commit()

        # Refresh pattern model
        update_pattern_performance(conn)
        print("[rank-check] Pattern model updated")


# ── Re-optimise underperforming pages ─────────────────────────────────────────

def reoptimise_pages(rank_threshold: int = 30, dry_run: bool = False):
    """
    Find pages ranked 11-threshold and rewrite them with a better keyword pattern.
    Only retries pages that haven't been reoptimised in 30+ days.
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT k.id, k.county, k.state, k.state_abbr, k.keyword,
                   k.rank, k.pattern_id
            FROM keywords k
            WHERE k.selected = 1
              AND k.rank IS NOT NULL
              AND k.rank BETWEEN 11 AND ?
              AND NOT EXISTS (
                  SELECT 1 FROM page_optimisation_log l
                  WHERE l.county = k.county AND l.state = k.state
                    AND l.created_at > datetime('now', '-30 days')
              )
            ORDER BY k.rank ASC
            LIMIT 25
        """, (rank_threshold,)).fetchall()

        if not rows:
            print("[reoptimise] No pages need reoptimisation right now")
            return

        best_pattern_id = get_best_pattern(conn)
        print(f"\n[reoptimise] {len(rows)} pages to try (best pattern: {best_pattern_id})")

        for row in rows:
            county, state, sa = row["county"], row["state"], row["state_abbr"]

            # Pick a pattern we haven't tried yet for this county
            tried_patterns = {r["pattern_id"] for r in conn.execute(
                "SELECT pattern_id FROM keywords WHERE county=? AND state=? AND pattern_id IS NOT NULL",
                (county, state)
            ).fetchall()}

            candidate_pattern_id = None
            for pid in [best_pattern_id] + list(range(len(PATTERNS))):
                if pid not in tried_patterns:
                    candidate_pattern_id = pid
                    break

            if candidate_pattern_id is None:
                print(f"  {county}, {state}: all patterns tried — skipping")
                continue

            new_keyword = PATTERNS[candidate_pattern_id].format(c=county, s=state)
            print(f"  {county}, {state}: rank #{row['rank']} → trying \"{new_keyword}\"")

            if not dry_run:
                # Deselect old, insert/select new
                conn.execute("UPDATE keywords SET selected=0 WHERE county=? AND state=? AND selected=1",
                             (county, state))
                conn.execute("""
                    INSERT INTO keywords
                    (county, state, state_abbr, keyword, pattern_id, source, score, selected)
                    VALUES (?, ?, ?, ?, ?, 'reoptimise', 60, 1)
                """, (county, state, sa, new_keyword, candidate_pattern_id))

                # Log it
                conn.execute("""
                    INSERT INTO page_optimisation_log
                    (county, state, old_keyword, new_keyword, old_rank, action)
                    VALUES (?, ?, ?, ?, ?, 'rewrite')
                """, (county, state, row["keyword"], new_keyword, row["rank"]))

                # Rewrite the HTML file
                _rewrite_page(county, state, sa, new_keyword)

        conn.commit()
        print("[reoptimise] Done")


def _rewrite_page(county: str, state: str, state_abbr: str, new_keyword: str):
    """Update the title, H1, and meta description in an existing county page."""
    slug = f"{county.lower().replace(' ', '-')}-county-{state.lower().replace(' ', '-')}-inmate-lookup.html"
    page_path = DIST_DIR / "counties" / slug
    if not page_path.exists():
        print(f"    [rewrite] file not found: {slug}")
        return

    html = page_path.read_text(encoding="utf-8", errors="replace")

    # Update <title>
    html = re.sub(
        r'<title>[^<]+</title>',
        f'<title>{new_keyword.title()} — Official Guide</title>',
        html, flags=re.I
    )
    # Update <h1>
    html = re.sub(
        r'<h1>[^<]+</h1>',
        f'<h1>{new_keyword.title()}</h1>',
        html, flags=re.I, count=1
    )
    # Update meta description
    html = re.sub(
        r'(<meta name="description" content=")[^"]*(")',
        f'\\1How to {new_keyword.lower()} — official sources, step-by-step guide, and bail information for {county} County, {state}.\\2',
        html, flags=re.I
    )

    page_path.write_text(html, encoding="utf-8")
    print(f"    [rewrite] ✓ {slug}")


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_report():
    """Print pattern leaderboard and overall stats."""
    with get_conn() as conn:
        print("\n" + "="*60)
        print("KEYWORD AGENT — PATTERN LEADERBOARD")
        print("="*60)

        patterns = conn.execute("""
            SELECT * FROM pattern_performance ORDER BY
            CASE WHEN median_rank IS NULL THEN 9999 ELSE median_rank END ASC
        """).fetchall()

        for p in patterns:
            if p["n_pages"] == 0:
                continue
            median = f"#{p['median_rank']:.0f}" if p["median_rank"] else "—"
            print(f"  [{p['pattern_id']}] {p['pattern'][:50]:<50} "
                  f"pages={p['n_pages']} ranked={p['n_ranked']} "
                  f"median={median} top10={p['top10_count']} top30={p['top30_count']}")

        total = conn.execute("SELECT COUNT(*) FROM keywords WHERE selected=1").fetchone()[0]
        ranked = conn.execute("SELECT COUNT(*) FROM keywords WHERE selected=1 AND rank IS NOT NULL").fetchone()[0]
        top10  = conn.execute("SELECT COUNT(*) FROM keywords WHERE selected=1 AND rank <= 10").fetchone()[0]
        top30  = conn.execute("SELECT COUNT(*) FROM keywords WHERE selected=1 AND rank <= 30").fetchone()[0]

        print(f"\n  Total researched: {total}")
        print(f"  Rank checked:     {ranked}")
        print(f"  Top 10:           {top10}")
        print(f"  Top 30:           {top30}")
        print("="*60)


def export_keyword_map(output_path: Optional[Path] = None) -> dict:
    """
    Export {county|state: selected_keyword} map for use by generate_pages.py.
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT county, state, state_abbr, keyword FROM keywords WHERE selected=1"
        ).fetchall()
    mapping = {f"{r['county']}|{r['state']}": r["keyword"] for r in rows}
    if output_path:
        output_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        print(f"[export] Wrote {len(mapping)} entries to {output_path}")
    return mapping


# ── CLI ────────────────────────────────────────────────────────────────────────

def load_counties(state_filter: str = None) -> list[tuple]:
    if CSV_PATH.exists():
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            counties = [(r["county"], r["state"], r["state_abbr"]) for r in reader]
    else:
        # Fallback: top counties
        counties = [
            ("Los Angeles", "California", "CA"), ("Cook", "Illinois", "IL"),
            ("Harris", "Texas", "TX"), ("Maricopa", "Arizona", "AZ"),
            ("San Diego", "California", "CA"), ("Dallas", "Texas", "TX"),
        ]
    if state_filter:
        counties = [c for c in counties if c[2].upper() == state_filter.upper()]
    return counties


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyword Research Agent — jailinmate.net")
    parser.add_argument("--county",       help="Single county name")
    parser.add_argument("--state",        help="State full name (e.g. Texas)")
    parser.add_argument("--state-abbr",   help="State abbreviation (e.g. TX)")
    parser.add_argument("--all-counties", action="store_true", help="Research all counties from CSV")
    parser.add_argument("--filter-state", help="Filter --all-counties to one state abbr")
    parser.add_argument("--rank-check",   action="store_true", help="Run DuckDuckGo rank checks")
    parser.add_argument("--rank-limit",   type=int, default=50, help="Max keywords to rank-check")
    parser.add_argument("--reoptimise",   action="store_true", help="Rewrite underperforming pages")
    parser.add_argument("--rank-threshold", type=int, default=30, help="Rank threshold for reoptimise")
    parser.add_argument("--dry-run",      action="store_true", help="Dry run (no file writes)")
    parser.add_argument("--report",       action="store_true", help="Print pattern leaderboard")
    parser.add_argument("--export",       action="store_true", help="Export keyword map JSON")
    parser.add_argument("--no-autocomplete", action="store_true", help="Skip Google Autocomplete")
    parser.add_argument("--batch-size",   type=int, default=20,  help="Counties per batch")
    parser.add_argument("--delay",        type=float, default=1.0, help="Delay between counties (s)")
    args = parser.parse_args()

    init_db()

    if args.report:
        update_pattern_performance(get_conn())
        print_report()

    elif args.export:
        out = DATA_DIR / "keyword_map.json"
        export_keyword_map(out)

    elif args.rank_check:
        run_rank_checks(limit=args.rank_limit)
        print_report()

    elif args.reoptimise:
        reoptimise_pages(rank_threshold=args.rank_threshold, dry_run=args.dry_run)

    elif args.county and args.state:
        sa = args.state_abbr or args.state[:2].upper()
        result = research_county(
            args.county, args.state, sa,
            use_autocomplete=not args.no_autocomplete
        )
        print(json.dumps(result, indent=2))

    elif args.all_counties:
        counties = load_counties(args.filter_state)
        print(f"[all-counties] Researching {len(counties)} counties…")
        for i, (county, state, sa) in enumerate(counties, 1):
            print(f"\n[{i}/{len(counties)}]", end="")
            research_county(county, state, sa,
                            use_autocomplete=not args.no_autocomplete)
            time.sleep(args.delay)
        export_keyword_map(DATA_DIR / "keyword_map.json")
        update_pattern_performance(get_conn())
        print_report()

    else:
        parser.print_help()
