"""
county_data_builder.py — Use Gemini to generate real sheriff/jail data for US counties.

Reads counties.csv, skips counties already in county_data.json,
generates real data via Gemini for the next batch (highest-population counties first),
validates and appends to county_data.json.

Usage:
    python county_data_builder.py --batch 50   # generate 50 counties
    python county_data_builder.py --batch 10 --dry-run
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

import google.generativeai as genai

# ── Config ────────────────────────────────────────────────────────────────────
DATA_FILE   = Path("county_data.json")
COUNTIES_CSV = Path("counties.csv")

# Top US counties by approximate population (for prioritization)
# Source: US Census 2020 estimates
TOP_COUNTIES_BY_POP = [
    ("Los Angeles", "California"), ("Cook", "Illinois"), ("Harris", "Texas"),
    ("Maricopa", "Arizona"), ("San Diego", "California"), ("Dallas", "Texas"),
    ("Orange", "California"), ("Kings", "New York"), ("Miami-Dade", "Florida"),
    ("Riverside", "California"), ("Clark", "Nevada"), ("Tarrant", "Texas"),
    ("San Bernardino", "California"), ("King", "Washington"), ("Bexar", "Texas"),
    ("Broward", "Florida"), ("Wayne", "Michigan"), ("Alameda", "California"),
    ("Middlesex", "Massachusetts"), ("Philadelphia", "Pennsylvania"),
    # Tier 1 continued
    ("Sacramento", "California"), ("Suffolk", "New York"), ("Queens", "New York"),
    ("New York", "New York"), ("Bronx", "New York"), ("Mecklenburg", "North Carolina"),
    ("Travis", "Texas"), ("Collin", "Texas"), ("Hillsborough", "Florida"),
    ("Oakland", "Michigan"), ("Orange", "Florida"), ("Nassau", "New York"),
    ("Shelby", "Tennessee"), ("Franklin", "Ohio"), ("Hennepin", "Minnesota"),
    ("Contra Costa", "California"), ("Wake", "North Carolina"), ("El Paso", "Texas"),
    ("Pima", "Arizona"), ("Cuyahoga", "Ohio"), ("Pinellas", "Florida"),
    ("Jefferson", "Alabama"), ("Palm Beach", "Florida"), ("Denver", "Colorado"),
    ("Hamilton", "Ohio"), ("Salt Lake", "Utah"), ("Montgomery", "Maryland"),
    ("Prince George's", "Maryland"), ("Essex", "New Jersey"), ("Hudson", "New Jersey"),
    ("Fulton", "Georgia"), ("DeKalb", "Georgia"), ("Gwinnett", "Georgia"),
    ("Duval", "Florida"), ("Multnomah", "Oregon"), ("Ada", "Idaho"),
    ("Milwaukee", "Wisconsin"), ("Erie", "New York"), ("Westchester", "New York"),
    ("Hartford", "Connecticut"), ("New Haven", "Connecticut"), ("Fairfield", "Connecticut"),
    ("Dane", "Wisconsin"), ("Bernalillo", "New Mexico"), ("Pinal", "Arizona"),
    ("Snohomish", "Washington"), ("Pierce", "Washington"), ("Spokane", "Washington"),
    ("Jefferson", "Colorado"), ("Arapahoe", "Colorado"), ("Adams", "Colorado"),
    ("El Paso", "Colorado"), ("Douglas", "Colorado"), ("Boulder", "Colorado"),
    ("Larimer", "Colorado"), ("Weld", "Colorado"), ("Pueblo", "Colorado"),
    ("Mesa", "Colorado"), ("Garfield", "Colorado"), ("Pitkin", "Colorado"),
    ("Summit", "Colorado"), ("Eagle", "Colorado"), ("Broomfield", "Colorado"),
    ("Chaffee", "Colorado"), ("Fremont", "Colorado"), ("Montrose", "Colorado"),
]

PROMPT = """You are a database of US county jail and sheriff information. 
Return ONLY a valid JSON object (no markdown, no explanation) with real, accurate data for:

County: {county}
State: {state}

Required JSON format (fill ALL fields with real data — no placeholders):
{{
  "county": "{county}",
  "state": "{state}",
  "state_abbr": "{state_abbr}",
  "sheriff_name": "Full official name of the sheriff's office or detention agency",
  "inmate_search_url": "https://... (exact URL of the official inmate roster/search page)",
  "sheriff_url": "https://... (official sheriff office website)",
  "jail_name": "Official name of the main county detention facility",
  "jail_address": "Full street address, City, State ZIP",
  "jail_phone": "(XXX) XXX-XXXX",
  "population": 000000,
  "doc_url": "https://... (state dept of corrections URL)",
  "court_url": "https://... (county superior/district court URL)",
  "notes": "1-2 sentences of useful context about this specific facility"
}}

Return ONLY the JSON object. No markdown fences. No extra text."""

STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}


def load_existing():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}


def save_data(data: dict):
    DATA_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def county_key(county: str, state: str) -> str:
    return f"{county}|{state}"


def generate_county_data(model, county: str, state: str) -> dict | None:
    abbr = STATE_ABBR.get(state, "")
    prompt = PROMPT.format(county=county, state=state, state_abbr=abbr)
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown fences if model adds them
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()
        data = json.loads(raw)
        # Validate required fields
        required = ["sheriff_name", "inmate_search_url", "jail_name", "jail_address", "jail_phone"]
        missing = [f for f in required if not data.get(f) or "placeholder" in str(data.get(f, "")).lower()]
        if missing:
            print(f"    WARNING: missing/placeholder fields: {missing}")
        return data
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        print(f"    Raw: {raw[:200]}")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=30, help="Counties to generate per run")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY or GEMINI_API_KEY")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    existing = load_existing()
    have_keys = set(existing.keys())
    print(f"Existing county data: {len(existing)}")

    # Build ordered list: TOP_COUNTIES first, then remaining from CSV
    ordered = []
    for county, state in TOP_COUNTIES_BY_POP:
        k = county_key(county, state)
        if k not in have_keys:
            ordered.append((county, state))

    # Add remaining from CSV if batch not filled
    if len(ordered) < args.batch:
        csv_lines = COUNTIES_CSV.read_text().strip().split("\n")[1:]
        for line in csv_lines:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                county, state = parts[0].strip(), parts[1].strip()
                k = county_key(county, state)
                if k not in have_keys and (county, state) not in ordered:
                    ordered.append((county, state))
            if len(ordered) >= args.batch * 3:
                break

    to_process = ordered[:args.batch]
    print(f"Generating data for {len(to_process)} counties...\n")

    added = 0
    errors = 0

    for county, state in to_process:
        key = county_key(county, state)
        print(f"  [{added+errors+1}/{len(to_process)}] {county}, {state} ...", end=" ", flush=True)

        if args.dry_run:
            print("DRY RUN")
            added += 1
            continue

        data = generate_county_data(model, county, state)
        if data:
            existing[key] = data
            save_data(existing)  # Save after each county (crash-safe)
            print(f"OK — {data.get('jail_name', '?')}")
            added += 1
        else:
            print("FAILED")
            errors += 1

        time.sleep(0.5)  # Rate limiting

    print(f"\nDone: {added} added, {errors} failed")
    print(f"Total county_data.json entries: {len(existing)}")


if __name__ == "__main__":
    main()
