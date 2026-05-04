"""
Patch scraper for team sports that Wikipedia categorizes by Games year, not by 'Olympic [Sport] for the United States'.

Walks 'Basketball players at the [year] Summer Olympics' and equivalents for volleyball,
basketball, baseball, soccer. Pages from these categories are international; we filter
to US athletes via birthplace_raw resolution downstream in aggregate.py (US-state lookup).

Output cache files (gitignored): data/raw/cache/by_games_year/{sport}_{year}.jsonl
Adds to the same /data/raw/athletes_us.jsonl on next compile_outputs run.

Run: python data/scrapers/wikipedia_team_sports_patch.py
"""
from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Allow imports from sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))

from wikipedia_team_usa import (
    AthleteRecord,
    CACHE_DIR,
    cat_members,
    extract_field,
    fetch_wikitext,
    slugify,
    REQUEST_SLEEP_S,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("patch")

SUMMER_YEARS = ["1936", "1948", "1952", "1956", "1960", "1964", "1968", "1972", "1976",
                "1980", "1984", "1988", "1992", "1996", "2000", "2004", "2008", "2012", "2016", "2020", "2024"]

SPORT_TO_CAT_FORMAT: dict[str, str] = {
    "Basketball": "Basketball players at the {year} Summer Olympics",
    "Volleyball": "Volleyball players at the {year} Summer Olympics",
    "Beach Volleyball": "Beach volleyball players at the {year} Summer Olympics",
    "Baseball": "Baseball players at the {year} Summer Olympics",
    "Softball": "Softball players at the {year} Summer Olympics",
    "Soccer": "Footballers at the {year} Summer Olympics",
    "Field Hockey": "Field hockey players at the {year} Summer Olympics",
    "Water Polo": "Water polo players at the {year} Summer Olympics",
    "Handball": "Handball players at the {year} Summer Olympics",
}


def patch_one(sport: str, year: str) -> int:
    cat = SPORT_TO_CAT_FORMAT[sport].format(year=year)
    cache_subdir = CACHE_DIR / "by_games_year"
    cache_subdir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_subdir / f"{slugify(sport)}_{year}.jsonl"
    if cache_path.exists():
        return -1

    try:
        pages = cat_members(cat, cmtype="page")
    except Exception as e:
        log.warning("  category miss: %s -> %s", cat, e)
        cache_path.write_text("", encoding="utf-8")
        return 0

    if not pages:
        cache_path.write_text("", encoding="utf-8")
        return 0

    titles = [p["title"] for p in pages]
    pageids = {p["title"]: p.get("pageid", 0) for p in pages}

    log.info("  %s %s -> %d pages, fetching wikitext", sport, year, len(pages))
    wt_map = fetch_wikitext(titles)

    records: list[AthleteRecord] = []
    for t in titles:
        info = wt_map.get(t)
        wt = info["wikitext"] if info else ""
        rec = AthleteRecord(
            page_title=t,
            page_id=pageids.get(t, 0),
            sport_category=sport,
            is_paralympic=False,
            birthplace_raw=extract_field(wt, r"birth_place|birthplace|placeofbirth"),
            hometown_raw=extract_field(wt, r"hometown|home_town|residence"),
            birth_date_raw=extract_field(wt, r"birth_date|birthdate|dateofbirth"),
        )
        records.append(rec)

    with cache_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    log.info("  -> wrote %d records to %s", len(records), cache_path.name)
    return len(records)


def compile_into_master() -> None:
    """Append by_games_year cache content into the master athletes_us.jsonl."""
    master = CACHE_DIR.parent / "athletes_us.jsonl"
    if not master.exists():
        log.error("master file %s missing — run main scraper first", master)
        return

    by_year_dir = CACHE_DIR / "by_games_year"
    if not by_year_dir.exists():
        log.warning("no by_games_year cache directory; nothing to merge")
        return

    n_added = 0
    with master.open("a", encoding="utf-8") as out:
        for f in sorted(by_year_dir.glob("*.jsonl")):
            content = f.read_text(encoding="utf-8")
            for line in content.splitlines():
                if not line.strip():
                    continue
                out.write(line + "\n")
                n_added += 1
    log.info("appended %d patch records into %s", n_added, master.name)


def main() -> int:
    log.info("team-sports patch starting")
    total_records = 0
    total_categories = 0
    for sport in SPORT_TO_CAT_FORMAT:
        for year in SUMMER_YEARS:
            total_categories += 1
            n = patch_one(sport, year)
            if n > 0:
                total_records += n
            time.sleep(REQUEST_SLEEP_S)
    log.info("scraped %d new athlete-records across %d categories", total_records, total_categories)
    compile_into_master()
    return 0


if __name__ == "__main__":
    sys.exit(main())
