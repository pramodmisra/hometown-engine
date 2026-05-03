"""
Aggregator: raw athlete records -> (state x sport x is_paralympic x count).

Reads:    data/raw/athletes_us.jsonl
Writes:   data/processed/athletes_aggregate.parquet
          data/processed/athletes_aggregate.csv  (for spot-check)
          data/processed/aggregate_quality_report.json

Place parsing: birthplace strings like "Providence, Rhode Island, United States"
or "Lubbock, Texas, U.S." are split on commas and matched against a 56-name
US state/territory list. Non-US places are dropped from aggregation but counted
in the quality report.

Sport normalization: a manual map gets the most common 94 categories to canonical
sport names; unmapped categories fall back to a stripped form.
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = DATA_DIR / "raw" / "athletes_us.jsonl"
OUT_DIR = DATA_DIR / "processed"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("aggregate")

US_STATES: dict[str, str] = {
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
    "District of Columbia": "DC", "Puerto Rico": "PR", "Guam": "GU",
    "American Samoa": "AS", "U.S. Virgin Islands": "VI", "Northern Mariana Islands": "MP",
}

US_INDICATORS = {
    "U.S.", "U.S.A.", "USA", "US", "United States", "United States of America", "America",
}

NON_US_COUNTRIES = {
    "Canada", "Mexico", "United Kingdom", "England", "Scotland", "Wales", "Ireland",
    "Australia", "New Zealand", "Germany", "France", "Italy", "Spain", "Russia",
    "China", "Japan", "Brazil", "Argentina", "Cuba", "Jamaica", "Kenya", "Ethiopia",
    "Somalia", "Nigeria", "South Africa", "Sweden", "Norway", "Denmark", "Finland",
    "Netherlands", "Belgium", "Switzerland", "Austria", "Poland", "Romania", "Greece",
    "Turkey", "Israel", "South Korea", "North Korea", "India", "Pakistan", "Vietnam",
    "Philippines", "Thailand", "Indonesia", "Egypt", "Morocco",
}


SPORT_CANONICAL_OLYMPIC: dict[str, str] = {
    "Archer": "Archery",
    "Track and field athlete": "Athletics",
    "Badminton player": "Badminton",
    "Baseball player": "Baseball",
    "3x3 basketball player": "3x3 Basketball",
    "Basketball player": "Basketball",
    "Beach volleyball player": "Beach Volleyball",
    "Boxer": "Boxing",
    "Breakdancer": "Breaking",
    "Canoeist": "Canoe",
    "Cyclist": "Cycling",
    "Diver": "Diving",
    "Equestrian": "Equestrian",
    "Fencer": "Fencing",
    "Field hockey player": "Field Hockey",
    "Golfer": "Golf",
    "Gymnast": "Gymnastics",
    "Handball player": "Handball",
    "Judoka": "Judo",
    "Karateka": "Karate",
    "Lacrosse player": "Lacrosse",
    "Modern pentathlete": "Modern Pentathlon",
    "Polo player": "Polo",
    "Real tennis player": "Real Tennis",
    "Roque player": "Roque",
    "Rower": "Rowing",
    "Rugby sevens player": "Rugby Sevens",
    "Rugby union player": "Rugby Union",
    "Sailor": "Sailing",
    "Shooter": "Shooting",
    "Skateboarder": "Skateboarding",
    "Soccer player": "Soccer",
    "Softball player": "Softball",
    "Sport climber": "Sport Climbing",
    "Surfer": "Surfing",
    "Swimmer": "Swimming",
    "Synchronized swimmer": "Artistic Swimming",
    "Table tennis player": "Table Tennis",
    "Taekwondo practitioner": "Taekwondo",
    "Tennis player": "Tennis",
    "Triathlete": "Triathlon",
    "Tug of war competitor": "Tug of War",
    "Volleyball player": "Volleyball",
    "Water polo player": "Water Polo",
    "Weightlifter": "Weightlifting",
    "Wrestler": "Wrestling",
    "Alpine skier": "Alpine Skiing",
    "Biathlete": "Biathlon",
    "Bobsledder": "Bobsleigh",
    "Cross-country skier": "Cross-Country Skiing",
    "Curler": "Curling",
    "Figure skater": "Figure Skating",
    "Freestyle skier": "Freestyle Skiing",
    "Ice hockey player": "Ice Hockey",
    "Luger": "Luge",
    "Nordic combined skier": "Nordic Combined",
    "Short-track speed skater": "Short Track Speed Skating",
    "Skeleton racer": "Skeleton",
    "Ski jumper": "Ski Jumping",
    "Ski mountaineer": "Ski Mountaineering",
    "Sled dog racer": "Sled Dog Racing",
    "Snowboarder": "Snowboarding",
    "Speed skater": "Speed Skating",
}

SPORT_CANONICAL_PARALYMPIC: dict[str, str] = {
    "Alpine skier": "Para Alpine Skiing",
    "Archer": "Para Archery",
    "Track and field athlete": "Para Athletics",
    "Badminton player": "Para Badminton",
    "Biathlete": "Para Biathlon",
    "Boccia player": "Boccia",
    "Canoeist": "Para Canoe",
    "Cross-country skier": "Para Cross-Country Skiing",
    "Wheelchair curler": "Wheelchair Curling",
    "Cyclist": "Para Cycling",
    "Equestrian": "Para Equestrian",
    "Wheelchair fencer": "Wheelchair Fencing",
    "Goalball player": "Goalball",
    "Sledge hockey player": "Para Ice Hockey",
    "Judoka": "Para Judo",
    "Powerlifter": "Para Powerlifting",
    "Rower": "Para Rowing",
    "Sailor": "Para Sailing",
    "Shooter": "Para Shooting",
    "Snowboarder": "Para Snowboarding",
    "Soccer player": "Para Football",
    "Swimmer": "Para Swimming",
    "Table tennis player": "Para Table Tennis",
    "Taekwondo practitioner": "Para Taekwondo",
    "Triathlete": "Para Triathlon",
    "Volleyball player": "Sitting Volleyball",
    "Wheelchair basketball player": "Wheelchair Basketball",
    "Wheelchair rugby player": "Wheelchair Rugby",
    "Wheelchair tennis player": "Wheelchair Tennis",
    "Wrestler": "Para Wrestling",
}


def canonical_sport(sport_category: str, is_paralympic: bool) -> str:
    """Map the scraper's normalized label + paralympic flag to a canonical sport name."""
    if not sport_category:
        return "Unknown"
    table = SPORT_CANONICAL_PARALYMPIC if is_paralympic else SPORT_CANONICAL_OLYMPIC
    if sport_category in table:
        return table[sport_category]
    prefix = "Para " if is_paralympic else ""
    return f"{prefix}{sport_category}"


_PUNCT_TO_STRIP = re.compile(r"[\[\]\{\}\"\(\)*]+")


def _clean_token(token: str) -> str:
    s = _PUNCT_TO_STRIP.sub("", token).strip(" .,;:|")
    s = re.sub(r"\s+", " ", s)
    return s


def parse_us_place(raw: str | None) -> tuple[str | None, str | None, bool]:
    """Return (city, state_name, is_us). Drops mid-string artifacts. Conservative."""
    if not raw:
        return None, None, False

    s = raw.replace("&nbsp;", " ").replace(" ", " ")
    s = re.sub(r"\{\{[^}]+\}\}", "", s)
    s = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    parts = [_clean_token(p) for p in s.split(",")]
    parts = [p for p in parts if p]
    if not parts:
        return None, None, False

    for p in parts:
        if p in NON_US_COUNTRIES:
            return None, None, False

    found_state: str | None = None
    state_idx: int | None = None
    for i, p in enumerate(parts):
        norm = p.replace(".", "").strip()
        for state_name, abbr in US_STATES.items():
            if p.lower() == state_name.lower() or norm.upper() == abbr:
                found_state = state_name
                state_idx = i
                break
        if found_state:
            break

    if found_state:
        city = None
        if state_idx is not None and state_idx > 0:
            candidate = parts[state_idx - 1]
            if 1 < len(candidate) < 60 and not any(c.isdigit() for c in candidate):
                city = candidate
        return city, found_state, True

    return None, None, False


def main() -> int:
    if not RAW_FILE.exists():
        log.error("missing %s — run scraper first", RAW_FILE)
        return 1

    rows: list[dict] = []
    with RAW_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rows.append(rec)
    log.info("loaded %d raw athlete records", len(rows))
    if not rows:
        return 1

    df = pd.DataFrame(rows)
    log.info("columns: %s", list(df.columns))

    df["sport"] = df.apply(lambda r: canonical_sport(r["sport_category"], bool(r["is_paralympic"])), axis=1)

    df["resolve_input"] = df["birthplace_raw"].fillna("").where(
        df["birthplace_raw"].astype(bool), df["hometown_raw"].fillna("")
    )

    parsed = df["resolve_input"].apply(parse_us_place)
    df["city"] = parsed.apply(lambda t: t[0])
    df["state"] = parsed.apply(lambda t: t[1])
    df["is_us_place"] = parsed.apply(lambda t: t[2])

    n_total = len(df)
    n_with_raw = int(df["resolve_input"].astype(bool).sum())
    n_us = int(df["is_us_place"].sum())
    n_state = int(df["state"].notna().sum())
    log.info(
        "place coverage: %d/%d have any raw, %d resolved to US, %d have state",
        n_with_raw, n_total, n_us, n_state,
    )

    df_dedup = df.dropna(subset=["state"]).copy()
    df_dedup = df_dedup.drop_duplicates(subset=["page_id", "sport", "is_paralympic"])
    log.info("after dedup on (page_id, sport, is_paralympic): %d rows", len(df_dedup))

    agg = (
        df_dedup
        .groupby(["state", "sport", "is_paralympic"], dropna=False)
        .size()
        .reset_index(name="athlete_count")
        .sort_values(["state", "athlete_count"], ascending=[True, False])
    )
    agg["state_code"] = agg["state"].map(US_STATES).fillna("XX")
    agg["data_source"] = "wikipedia_categories_v1"
    agg = agg[["state", "state_code", "sport", "is_paralympic", "athlete_count", "data_source"]]
    log.info("aggregated to %d (state, sport, is_paralympic) rows", len(agg))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = OUT_DIR / "athletes_aggregate.parquet"
    csv_path = OUT_DIR / "athletes_aggregate.csv"
    agg.to_parquet(parquet_path, index=False)
    agg.to_csv(csv_path, index=False)
    log.info("wrote %s and %s", parquet_path.name, csv_path.name)

    quality = {
        "raw_records": n_total,
        "with_any_place_string": n_with_raw,
        "resolved_to_us": n_us,
        "with_state": n_state,
        "deduplicated_us_records": len(df_dedup),
        "aggregate_rows": len(agg),
        "olympic_aggregate_rows": int((agg["is_paralympic"] == False).sum()),
        "paralympic_aggregate_rows": int((agg["is_paralympic"] == True).sum()),
        "states_represented": int(agg["state"].nunique()),
        "sports_olympic": int(agg.loc[agg["is_paralympic"] == False, "sport"].nunique()),
        "sports_paralympic": int(agg.loc[agg["is_paralympic"] == True, "sport"].nunique()),
        "top_10_olympic_states": (
            agg[agg["is_paralympic"] == False]
            .groupby("state")["athlete_count"].sum()
            .sort_values(ascending=False)
            .head(10).to_dict()
        ),
        "top_10_paralympic_states": (
            agg[agg["is_paralympic"] == True]
            .groupby("state")["athlete_count"].sum()
            .sort_values(ascending=False)
            .head(10).to_dict()
        ),
    }
    quality_path = OUT_DIR / "aggregate_quality_report.json"
    quality_path.write_text(json.dumps(quality, indent=2, default=int), encoding="utf-8")
    log.info("wrote quality report -> %s", quality_path.name)

    sport_counts = Counter(df["sport"])
    log.info("top 10 sports by raw record count:")
    for s, n in sport_counts.most_common(10):
        log.info("  %-30s %d", s, n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
