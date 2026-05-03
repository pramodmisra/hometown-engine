"""
Wikidata SPARQL probe v2 — broader Paralympic detection, cheaper queries.

Tries:
  - Paralympics via "participant in" any Paralympic Games event (P1344) instead of occupation P106
  - State via "located in admin entity" P131 ONE level (no transitive *)
"""
from __future__ import annotations

import json
import sys
import time

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "HometownEngineHackathon/0.1 (https://github.com/pramodmisra/hometown-engine)"


def sparql(q: str, timeout: int = 90) -> dict:
    h = {"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    r = requests.get(ENDPOINT, params={"query": q, "format": "json"}, headers=h, timeout=timeout)
    r.raise_for_status()
    return r.json()


def count_us_paralympians_via_participation() -> int:
    # Q193708 = Paralympic Games (parent event class). Find athletes who participated in
    # an event whose instance-of (transitively) is Paralympic Games and whose
    # citizenship is USA.
    q = """
    SELECT (COUNT(DISTINCT ?athlete) AS ?n) WHERE {
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P1344 ?event .
      ?event (wdt:P31/wdt:P279*) wd:Q193708 .
    }
    """
    return int(sparql(q)["results"]["bindings"][0]["n"]["value"])


def count_us_olympians_via_participation() -> int:
    # Q5389 = Olympic Games
    q = """
    SELECT (COUNT(DISTINCT ?athlete) AS ?n) WHERE {
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P1344 ?event .
      ?event (wdt:P31/wdt:P279*) wd:Q5389 .
    }
    """
    return int(sparql(q)["results"]["bindings"][0]["n"]["value"])


def list_paralympians_with_sport_and_birthplace(limit: int = 5000) -> list[dict]:
    q = f"""
    SELECT ?athlete ?athleteLabel ?sportLabel ?placeOfBirthLabel ?stateLabel WHERE {{
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P1344 ?event ;
               wdt:P641 ?sport .
      ?event (wdt:P31/wdt:P279*) wd:Q193708 .
      OPTIONAL {{ ?athlete wdt:P19 ?placeOfBirth . }}
      OPTIONAL {{ ?placeOfBirth wdt:P131 ?state . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    LIMIT {limit}
    """
    rows = []
    for b in sparql(q, timeout=120)["results"]["bindings"]:
        rows.append({
            "qid": b["athlete"]["value"].rsplit("/", 1)[-1],
            "name": b.get("athleteLabel", {}).get("value", ""),
            "sport": b.get("sportLabel", {}).get("value", ""),
            "birthplace": b.get("placeOfBirthLabel", {}).get("value", ""),
            "state": b.get("stateLabel", {}).get("value", ""),
        })
    return rows


def list_olympians_with_sport_and_birthplace(limit: int = 20000) -> list[dict]:
    q = f"""
    SELECT ?athlete ?athleteLabel ?sportLabel ?placeOfBirthLabel ?stateLabel WHERE {{
      ?athlete wdt:P27 wd:Q30 ;
               wdt:P1344 ?event ;
               wdt:P641 ?sport ;
               wdt:P19 ?placeOfBirth .
      ?event (wdt:P31/wdt:P279*) wd:Q5389 .
      OPTIONAL {{ ?placeOfBirth wdt:P131 ?state . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    LIMIT {limit}
    """
    rows = []
    for b in sparql(q, timeout=180)["results"]["bindings"]:
        rows.append({
            "qid": b["athlete"]["value"].rsplit("/", 1)[-1],
            "name": b.get("athleteLabel", {}).get("value", ""),
            "sport": b.get("sportLabel", {}).get("value", ""),
            "birthplace": b.get("placeOfBirthLabel", {}).get("value", ""),
            "state": b.get("stateLabel", {}).get("value", ""),
        })
    return rows


def main() -> int:
    print("WIKIDATA v2 PROBE")
    print("=" * 60)

    print("[A] US Paralympians via P1344 participation in Paralympic Games event ...")
    n_para = count_us_paralympians_via_participation()
    print(f"    -> {n_para:,}")
    time.sleep(1)

    print("[B] US Olympians via P1344 participation in Olympic Games event ...")
    n_oly = count_us_olympians_via_participation()
    print(f"    -> {n_oly:,}")
    time.sleep(1)

    print("[C] Pull Paralympians with sport + birthplace ...")
    para = list_paralympians_with_sport_and_birthplace()
    with_state = sum(1 for r in para if r["state"])
    with_birth = sum(1 for r in para if r["birthplace"])
    print(f"    -> {len(para)} rows, {with_birth} have birthplace, {with_state} have state")

    if para[:5]:
        print("    Sample 5:")
        for r in para[:5]:
            print(f"      {r['name'][:30]:30s} | {r['sport'][:20]:20s} | {r['birthplace'][:25]:25s} | {r['state'][:20]}")
    time.sleep(2)

    print("[D] Pull Olympians with sport + birthplace ...")
    oly = list_olympians_with_sport_and_birthplace()
    oly_with_state = sum(1 for r in oly if r["state"])
    print(f"    -> {len(oly)} rows, {oly_with_state} have state")

    out = {
        "counts": {"olympic_p1344": n_oly, "paralympic_p1344": n_para},
        "olympic_records": oly,
        "paralympic_records": para,
    }
    import pathlib
    p = pathlib.Path(__file__).parent / "wikidata_v2_records.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved {len(oly) + len(para):,} records -> {p}")

    print("\nVERDICT:")
    if n_para < 100:
        print(f"  Paralympic count {n_para} -> INSUFFICIENT. Pivot to Wikipedia categories or NPC USA pages.")
    if oly_with_state < len(oly) * 0.5:
        print(f"  State resolution {oly_with_state}/{len(oly)} -> need geocoding fallback (Census place-name lookup).")
    if n_oly > 5000 and oly_with_state > 1000:
        print("  Olympic coverage is workable with geocoding cleanup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
