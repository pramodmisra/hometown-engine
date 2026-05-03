"""
Wikipedia category probe — does Wikipedia maintain curated US Olympian/Paralympian categories?

We need a defensible source for aggregate counts at (region x sport x is_paralympic).
Wikipedia categories are CC BY-SA 4.0 / GFDL — fine for derived aggregates.
"""
from __future__ import annotations

import json
import time

import requests

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "HometownEngineHackathon/0.1 (https://github.com/pramodmisra/hometown-engine)"


def cat_members(category: str, cmtype: str = "page|subcat", limit: int = 500) -> list[dict]:
    out = []
    cont = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": str(limit),
            "cmtype": cmtype,
            "format": "json",
            "cmprop": "ids|title|type",
        }
        if cont:
            params["cmcontinue"] = cont
        r = requests.get(API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        j = r.json()
        out.extend(j["query"]["categorymembers"])
        cont = j.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        time.sleep(0.5)
    return out


def count_pages(category: str) -> int:
    members = cat_members(category, cmtype="page")
    return len(members)


def main() -> None:
    print("WIKIPEDIA CATEGORY PROBE")
    print("=" * 60)

    candidates_olympic = [
        "Olympic_competitors_for_the_United_States",
        "American_Olympic_competitors",
        "Olympic_athletes_for_the_United_States",
    ]
    candidates_paralympic = [
        "Paralympic_competitors_for_the_United_States",
        "American_Paralympic_competitors",
        "Paralympic_athletes_for_the_United_States",
    ]

    print("\n[A] Olympic root categories — direct page count:")
    for cat in candidates_olympic:
        try:
            n = count_pages(cat)
            print(f"    {cat:60s} -> {n} direct pages")
        except Exception as e:
            print(f"    {cat:60s} -> ERROR {e}")

    print("\n[B] Paralympic root categories — direct page count:")
    for cat in candidates_paralympic:
        try:
            n = count_pages(cat)
            print(f"    {cat:60s} -> {n} direct pages")
        except Exception as e:
            print(f"    {cat:60s} -> ERROR {e}")

    print("\n[C] Olympic — list direct subcats (sport buckets) from likely root ...")
    for cat in candidates_olympic:
        try:
            subs = cat_members(cat, cmtype="subcat")
            if subs:
                print(f"    Root: {cat} -> {len(subs)} subcats:")
                for s in subs[:30]:
                    print(f"      - {s['title']}")
                if len(subs) > 30:
                    print(f"      ... +{len(subs) - 30} more")
                break
        except Exception as e:
            print(f"    {cat} ERROR {e}")

    print("\n[D] Paralympic — list direct subcats from likely root ...")
    for cat in candidates_paralympic:
        try:
            subs = cat_members(cat, cmtype="subcat")
            if subs:
                print(f"    Root: {cat} -> {len(subs)} subcats:")
                for s in subs[:30]:
                    print(f"      - {s['title']}")
                if len(subs) > 30:
                    print(f"      ... +{len(subs) - 30} more")
                break
        except Exception as e:
            print(f"    {cat} ERROR {e}")

    print("\n[E] Pick a sport-specific category and count members (sanity check):")
    sport_cats = [
        "American_Olympic_swimmers",
        "American_male_Olympic_swimmers",
        "American_Olympic_track_and_field_athletes",
        "Track_and_field_athletes_at_the_2024_Summer_Olympics_for_the_United_States",
        "American_Paralympic_swimmers",
        "American_Paralympic_track_and_field_athletes",
        "Paralympic_track_and_field_athletes_for_the_United_States",
        "Paralympic_swimmers_for_the_United_States",
    ]
    for cat in sport_cats:
        try:
            n = count_pages(cat)
            print(f"    {cat:65s} -> {n} pages")
        except Exception as e:
            print(f"    {cat:65s} -> ERROR {e}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
