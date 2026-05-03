"""
Validate the athletes_aggregate against expected Team USA hubs.

Spot-checks 10 widely-known regions to confirm the aggregate captures
reasonable signal. State grain only (Day 2 baseline); city/county checks
will come once we have geocoded city-level grain.

Reads either the local Parquet (preferred) or BigQuery if --remote.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent
PARQUET = DATA_DIR / "processed" / "athletes_aggregate.parquet"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("validate")


HUB_EXPECTATIONS: list[dict] = [
    {"state": "Oregon",        "lens": "Athletics",                 "min_count": 10, "context": "Eugene/Hayward Field — distance running"},
    {"state": "California",    "lens": "Swimming",                  "min_count": 50, "context": "Stanford/UCLA/UCSB swim hub"},
    {"state": "Colorado",      "lens": "Cross-Country Skiing",      "min_count": 5,  "context": "Vail/Steamboat — winter endurance"},
    {"state": "Utah",          "lens": "Alpine Skiing",             "min_count": 5,  "context": "Park City — winter base"},
    {"state": "New York",      "lens": "Figure Skating",            "min_count": 5,  "context": "Lake Placid — winter sports legacy"},
    {"state": "New York",      "lens": "Bobsleigh",                 "min_count": 10, "context": "Lake Placid bobsled track"},
    {"state": "Minnesota",     "lens": "Ice Hockey",                "min_count": 30, "context": "hockey culture"},
    {"state": "Texas",         "lens": "Athletics",                 "min_count": 25, "context": "track and field powerhouse"},
    {"state": "California",    "lens": "Para Athletics",            "min_count": 5,  "context": "Chula Vista training center area"},
    {"state": "Illinois",      "lens": "Para Athletics",            "min_count": 1,  "context": "Champaign-Urbana adaptive sports"},
]


KNOWN_GAPS: list[str] = [
    "Basketball: Wikipedia uses 'Basketball at the [year] Summer Olympics' rather than 'Olympic basketball players for the United States'. Recursion at depth=2 from the Team USA root does not reach those categories. Day 3 task: add a manual scrape pass over the by-Games-year basketball/volleyball/baseball categories.",
    "Florida Swimming: Wikipedia birthplace metadata is biased toward where athletes were born, not where they trained. Many 'Florida' swimmers were born elsewhere (e.g., Lochte was born in NY; Phelps in MD). Day 3 task: enrich with hometown field as a secondary signal beyond birth_place.",
    "Climate precipitation: NOAA GSOD station-day records undercount real annual precipitation by ~24% due to missing-day handling. Acceptable for relative comparisons in narratives, but document caveat in UI.",
]


def load_aggregate(parquet_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path)
    df.columns = [c.lower() for c in df.columns]
    return df


def check_hub(df: pd.DataFrame, hub: dict) -> dict:
    sub = df[(df["state"].str.lower() == hub["state"].lower())
             & (df["sport"].str.lower() == hub["lens"].lower())]
    actual = int(sub["athlete_count"].sum())
    passed = actual >= hub["min_count"]
    return {**hub, "actual_count": actual, "passed": passed}


def state_top_sports(df: pd.DataFrame, state: str, n: int = 5) -> list[tuple[str, int, bool]]:
    sub = df[df["state"].str.lower() == state.lower()]
    top = (sub.groupby(["sport", "is_paralympic"])["athlete_count"].sum()
            .sort_values(ascending=False).head(n))
    return [(idx[0], int(v), bool(idx[1])) for idx, v in top.items()]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parquet", default=str(PARQUET), help="path to aggregate parquet")
    args = p.parse_args(argv)

    pq = Path(args.parquet)
    if not pq.exists():
        log.error("missing %s", pq)
        return 1

    df = load_aggregate(pq)
    log.info("loaded aggregate: %d rows, %d states, %d sports",
             len(df), df["state"].nunique(), df["sport"].nunique())

    log.info("\n=== HUB EXPECTATION CHECKS ===")
    pass_count = 0
    for hub in HUB_EXPECTATIONS:
        r = check_hub(df, hub)
        flag = "PASS" if r["passed"] else "FAIL"
        log.info("[%s] %-12s %-25s actual=%d (min=%d) — %s",
                 flag, hub["state"], hub["lens"], r["actual_count"], hub["min_count"], hub["context"])
        if r["passed"]:
            pass_count += 1
    log.info("\nSummary: %d / %d hub expectations passed", pass_count, len(HUB_EXPECTATIONS))

    log.info("\n=== KNOWN DATA GAPS (acknowledge in product UI) ===")
    for g in KNOWN_GAPS:
        log.info("  - %s", g)

    log.info("\n=== TOP SPORTS PER REPRESENTATIVE STATE (Olympic AND Paralympic side by side) ===")
    for state in ["California", "Texas", "Oregon", "Colorado", "Illinois", "New York"]:
        log.info("\n%s — top 5 (sport, count, is_paralympic):", state)
        for sport, count, is_para in state_top_sports(df, state):
            kind = "Para" if is_para else "Oly "
            log.info("  %s %-30s %d", kind, sport, count)

    log.info("\n=== TOP 10 PARALYMPIC STATES (sanity check) ===")
    para = df[df["is_paralympic"] == True].groupby("state")["athlete_count"].sum().sort_values(ascending=False).head(10)
    for state, count in para.items():
        log.info("  %-20s %d", state, count)

    return 0


if __name__ == "__main__":
    sys.exit(main())
