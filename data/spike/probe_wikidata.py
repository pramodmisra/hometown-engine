"""
Wikidata SPARQL probe — Day 1 data spike.

Goal: confirm Wikidata can return aggregate (region x sport x is_paralympic x count)
data for Team USA Olympians and Paralympians. CC0 license, defensible source.

Run: python probe_wikidata.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "HometownEngineHackathon/0.1 (https://github.com/pramodmisra/hometown-engine)"
OUT_DIR = Path(__file__).parent

# Q5482740 = Olympic athlete; Q53831 = Olympic Games; Q201195 = Paralympics
# wdt:P27 = country of citizenship; wd:Q30 = United States of America
# wdt:P641 = sport; wdt:P19 = place of birth; wdt:P1532 = country for sport (less reliable)
# wdt:P166 = award received; wdt:P1344 = participant in (event)


def run_sparql(query: str, timeout: int = 90) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    r = requests.get(ENDPOINT, params={"query": query, "format": "json"}, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def probe_count_us_olympians() -> int:
    q = """
    SELECT (COUNT(DISTINCT ?athlete) AS ?n) WHERE {
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P106 wd:Q11338576 .
    }
    """
    j = run_sparql(q)
    return int(j["results"]["bindings"][0]["n"]["value"])


def probe_count_us_paralympians() -> int:
    q = """
    SELECT (COUNT(DISTINCT ?athlete) AS ?n) WHERE {
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P106 wd:Q14085943 .
    }
    """
    j = run_sparql(q)
    return int(j["results"]["bindings"][0]["n"]["value"])


def sample_olympians_by_sport_and_birthplace(limit: int = 50) -> list[dict]:
    q = f"""
    SELECT ?athlete ?athleteLabel ?sportLabel ?placeOfBirthLabel ?stateLabel WHERE {{
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P106 wd:Q11338576 ;
               wdt:P641 ?sport ;
               wdt:P19 ?placeOfBirth .
      OPTIONAL {{ ?placeOfBirth wdt:P131 ?state . ?state wdt:P31/wdt:P279* wd:Q35657 . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    LIMIT {limit}
    """
    j = run_sparql(q)
    rows = []
    for b in j["results"]["bindings"]:
        rows.append({
            "athlete_qid": b["athlete"]["value"].rsplit("/", 1)[-1],
            "name": b.get("athleteLabel", {}).get("value", ""),
            "sport": b.get("sportLabel", {}).get("value", ""),
            "birthplace": b.get("placeOfBirthLabel", {}).get("value", ""),
            "state": b.get("stateLabel", {}).get("value", ""),
        })
    return rows


def aggregate_us_olympians_by_state_and_sport(limit: int = 5000) -> list[dict]:
    """Get aggregate counts: state x sport x count. No individual records returned."""
    q = f"""
    SELECT ?stateLabel ?sportLabel (COUNT(DISTINCT ?athlete) AS ?n) WHERE {{
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P106 wd:Q11338576 ;
               wdt:P641 ?sport ;
               wdt:P19 ?placeOfBirth .
      ?placeOfBirth wdt:P131* ?state .
      ?state wdt:P31/wdt:P279* wd:Q35657 .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    GROUP BY ?stateLabel ?sportLabel
    HAVING (COUNT(DISTINCT ?athlete) >= 2)
    ORDER BY DESC(?n)
    LIMIT {limit}
    """
    j = run_sparql(q, timeout=120)
    return [
        {
            "state": b.get("stateLabel", {}).get("value", ""),
            "sport": b.get("sportLabel", {}).get("value", ""),
            "athlete_count": int(b["n"]["value"]),
            "is_paralympic": False,
        }
        for b in j["results"]["bindings"]
    ]


def aggregate_us_paralympians_by_state_and_sport(limit: int = 5000) -> list[dict]:
    q = f"""
    SELECT ?stateLabel ?sportLabel (COUNT(DISTINCT ?athlete) AS ?n) WHERE {{
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P106 wd:Q14085943 ;
               wdt:P641 ?sport ;
               wdt:P19 ?placeOfBirth .
      ?placeOfBirth wdt:P131* ?state .
      ?state wdt:P31/wdt:P279* wd:Q35657 .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    GROUP BY ?stateLabel ?sportLabel
    ORDER BY DESC(?n)
    LIMIT {limit}
    """
    j = run_sparql(q, timeout=120)
    return [
        {
            "state": b.get("stateLabel", {}).get("value", ""),
            "sport": b.get("sportLabel", {}).get("value", ""),
            "athlete_count": int(b["n"]["value"]),
            "is_paralympic": True,
        }
        for b in j["results"]["bindings"]
    ]


def main() -> int:
    print("=" * 60)
    print("WIKIDATA PROBE — Day 1 data spike for Hometown Engine")
    print("=" * 60)

    print("\n[1] Counting US Olympians (occupation = Olympic athlete) ...")
    try:
        n_oly = probe_count_us_olympians()
        print(f"    -> {n_oly:,} US Olympians in Wikidata")
    except Exception as e:
        print(f"    FAIL: {e}")
        return 1
    time.sleep(1)

    print("\n[2] Counting US Paralympians (occupation = Paralympic athlete) ...")
    try:
        n_para = probe_count_us_paralympians()
        print(f"    -> {n_para:,} US Paralympians in Wikidata")
    except Exception as e:
        print(f"    FAIL: {e}")
        return 1
    time.sleep(1)

    print("\n[3] Sample 50 Olympians with sport + birthplace + state ...")
    try:
        sample = sample_olympians_by_sport_and_birthplace(50)
        with_state = sum(1 for r in sample if r["state"])
        print(f"    -> {len(sample)} sample rows, {with_state} have a state resolved")
        if sample:
            print(f"    First 3: {json.dumps(sample[:3], indent=2)}")
    except Exception as e:
        print(f"    FAIL: {e}")
        return 1
    time.sleep(2)

    print("\n[4] Aggregate US Olympians by state x sport (count >= 2) ...")
    try:
        oly_agg = aggregate_us_olympians_by_state_and_sport()
        print(f"    -> {len(oly_agg)} (state, sport) Olympic rows")
        if oly_agg:
            print("    Top 10 by count:")
            for r in oly_agg[:10]:
                print(f"      {r['state']:30s} | {r['sport']:25s} | {r['athlete_count']}")
    except Exception as e:
        print(f"    FAIL: {e}")
        return 1
    time.sleep(2)

    print("\n[5] Aggregate US Paralympians by state x sport ...")
    try:
        para_agg = aggregate_us_paralympians_by_state_and_sport()
        print(f"    -> {len(para_agg)} (state, sport) Paralympic rows")
        if para_agg:
            print("    Top 10 by count:")
            for r in para_agg[:10]:
                print(f"      {r['state']:30s} | {r['sport']:25s} | {r['athlete_count']}")
    except Exception as e:
        print(f"    FAIL: {e}")
        return 1

    out = OUT_DIR / "wikidata_aggregate.json"
    out.write_text(json.dumps({"olympic": oly_agg, "paralympic": para_agg}, indent=2), encoding="utf-8")
    print(f"\nSaved aggregates -> {out}")

    print("\nVERDICT:")
    para_total = sum(r["athlete_count"] for r in para_agg)
    oly_total = sum(r["athlete_count"] for r in oly_agg)
    print(f"  Olympic     athletes covered (state-resolved): {oly_total:,}")
    print(f"  Paralympic  athletes covered (state-resolved): {para_total:,}")
    if para_total < 50:
        print("  WARN: Paralympic coverage is thin in Wikidata. Need fallback (Wikipedia, NPC USA pages).")
    if oly_total < 1000:
        print("  WARN: Olympic coverage thin too — birthplace/state resolution may be lossy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
