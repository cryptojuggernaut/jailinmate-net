"""
bulk_keyword_research.py
Fast bulk keyword assignment — no autocomplete, just pattern-based scoring.
Only processes counties not yet in the DB.
"""
import sqlite3, csv, time, json
from pathlib import Path

PROJECT_DIR = Path(r'C:\WebAutomation\projects\inmate-lookup-site')
DB_PATH     = PROJECT_DIR / 'keyword_data' / 'keywords.db'
CSV_PATH    = PROJECT_DIR / 'counties.csv'

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

POSITIVE = ["inmate lookup","inmate search","jail roster","jail records","arrest records",
            "who's in jail","inmate locator","detention","mugshot","booking","county jail"]
NEGATIVE = ["death row","federal","sex offender","wikipedia","how to become","salary","officer","commissioner"]

def score(kw, county, state):
    k = kw.lower()
    s = 50.0
    if county.lower() in k: s += 15
    if state.lower() in k or state.lower()[:4] in k: s += 8
    for p in POSITIVE:
        if p in k: s += 12; break
    for n in NEGATIVE:
        if n in k: s -= 30
    words = k.split()
    if len(words) < 3: s -= 20
    elif len(words) > 8: s -= 10
    return max(0.0, min(100.0, s))

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        county TEXT NOT NULL, state TEXT NOT NULL, state_abbr TEXT NOT NULL,
        keyword TEXT NOT NULL, pattern_id INTEGER,
        source TEXT DEFAULT 'generated', score REAL DEFAULT 0,
        selected INTEGER DEFAULT 0, rank INTEGER,
        rank_checked_at TEXT, rank_history TEXT DEFAULT '[]',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS pattern_performance (
        pattern_id INTEGER PRIMARY KEY, pattern TEXT NOT NULL,
        n_pages INTEGER DEFAULT 0, n_ranked INTEGER DEFAULT 0,
        median_rank REAL, top10_count INTEGER DEFAULT 0, top30_count INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS page_optimisation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        county TEXT NOT NULL, state TEXT NOT NULL,
        old_keyword TEXT, new_keyword TEXT, old_rank INTEGER,
        action TEXT, created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_kw_county ON keywords(county, state);
    CREATE INDEX IF NOT EXISTS idx_kw_selected ON keywords(selected);
    """)
    conn.commit()

def get_done(conn):
    rows = conn.execute("SELECT county||'|'||state FROM keywords WHERE selected=1").fetchall()
    return {r[0] for r in rows}

def research_county(conn, county, state, state_abbr):
    candidates = []
    for i, pat in enumerate(PATTERNS):
        kw = pat.format(c=county, s=state)
        candidates.append({
            'keyword': kw, 'pattern_id': i,
            'source': 'generated', 'score': score(kw, county, state)
        })
    candidates.sort(key=lambda x: x['score'], reverse=True)
    winner = candidates[0]

    for c in candidates:
        conn.execute("""
            INSERT INTO keywords (county,state,state_abbr,keyword,pattern_id,source,score,selected)
            VALUES (?,?,?,?,?,?,?,?)
        """, (county, state, state_abbr, c['keyword'], c['pattern_id'],
              c['source'], c['score'], 1 if c['keyword'] == winner['keyword'] else 0))
    return winner

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    init_db(conn)
    done = get_done(conn)
    print(f"Already done: {len(done)} counties")

    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        all_counties = list(csv.DictReader(f))

    todo = [(r['county'], r['state'], r['state_abbr'])
            for r in all_counties if f"{r['county']}|{r['state']}" not in done]
    print(f"To research: {len(todo)} counties")

    for i, (county, state, sa) in enumerate(todo, 1):
        winner = research_county(conn, county, state, sa)
        if i % 100 == 0:
            conn.commit()
            print(f"  [{i}/{len(todo)}] last: {county}, {state} -> \"{winner['keyword']}\"")

    conn.commit()

    # Export keyword map
    rows = conn.execute("SELECT county, state, state_abbr, keyword FROM keywords WHERE selected=1").fetchall()
    mapping = {f"{r['county']}|{r['state']}": r['keyword'] for r in rows}
    out_path = DB_PATH.parent / 'keyword_map.json'
    out_path.write_text(json.dumps(mapping, indent=2), encoding='utf-8')

    total_done = conn.execute("SELECT COUNT(*) FROM keywords WHERE selected=1").fetchone()[0]
    print(f"\n[DONE] {total_done} counties in DB")
    print(f"[DONE] keyword_map.json written ({len(mapping)} entries)")
    conn.close()

if __name__ == '__main__':
    main()
