"""Find Wikipedia category names that hold US Olympic basketball/volleyball/baseball/soccer players."""
from __future__ import annotations

import time
import requests

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "HometownEngineHackathon/0.1 (https://github.com/pramodmisra/hometown-engine)"


def search_categories(query: str, limit: int = 25) -> list[dict]:
    params = {
        "action": "query",
        "list": "search",
        "srnamespace": "14",
        "srsearch": query,
        "srlimit": str(limit),
        "format": "json",
        "formatversion": "2",
    }
    r = requests.get(API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    return r.json().get("query", {}).get("search", [])


def cat_member_count(category: str) -> int:
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": "500",
        "cmtype": "page",
        "cmnamespace": "0",
        "format": "json",
        "formatversion": "2",
    }
    n = 0
    cont = None
    while True:
        if cont:
            params["cmcontinue"] = cont
        r = requests.get(API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        j = r.json()
        n += len(j.get("query", {}).get("categorymembers", []))
        cont = j.get("continue", {}).get("cmcontinue")
        time.sleep(0.3)
        if not cont:
            break
    return n


def main() -> None:
    queries = [
        "Basketball at the Summer Olympics United States",
        "United States men's national basketball team",
        "United States women's national basketball team",
        "United States men's national soccer team",
        "United States women's national soccer team",
        "United States men's national volleyball team",
        "Basketball players at the Summer Olympics",
        "Volleyball players at the Summer Olympics",
    ]
    for q in queries:
        print(f"\n=== query: {q!r} ===")
        try:
            results = search_categories(q, limit=10)
            for r in results[:8]:
                title = r["title"].replace("Category:", "")
                cnt = cat_member_count(title)
                print(f"  {cnt:4d}  {title}")
        except Exception as e:
            print(f"  ERROR {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
