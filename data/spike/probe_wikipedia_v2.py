"""
Wikipedia probe v2 — confirm Olympic sport subcats + birthplace extractability.

Goals:
  1. Walk Summer/Winter Olympics for US -> find sport subcategories
  2. Pick a few athlete pages and extract birth_place infobox field via wikitext
  3. Decide: is this a viable, defensible source for aggregate (state x sport x count)?
"""
from __future__ import annotations

import json
import re
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
        time.sleep(0.3)
    return out


def fetch_wikitext(titles: list[str]) -> dict[str, str]:
    """Batch fetch wikitext for up to 50 page titles. Returns {title: wikitext}."""
    out: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        batch = titles[i : i + 50]
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": "|".join(batch),
            "format": "json",
            "formatversion": "2",
        }
        r = requests.get(API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        for p in r.json()["query"]["pages"]:
            if "revisions" in p:
                out[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
        time.sleep(0.3)
    return out


BIRTHPLACE_RE = re.compile(r"\|\s*(?:birth_place|birthplace|placeofbirth|hometown)\s*=\s*([^\n|}]+)", re.IGNORECASE)


def extract_birthplace(wikitext: str) -> str | None:
    m = BIRTHPLACE_RE.search(wikitext)
    if not m:
        return None
    raw = m.group(1).strip()
    raw = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = re.sub(r"\{\{[^}]+\}\}", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" ,")
    return raw or None


def main() -> None:
    print("WIKIPEDIA PROBE v2")
    print("=" * 60)

    print("\n[A] Walk Summer Olympics competitors for the US -> sport subcats:")
    summer_subs = cat_members("Summer_Olympics_competitors_for_the_United_States", cmtype="subcat")
    print(f"    {len(summer_subs)} subcats. Sample (first 30):")
    for s in summer_subs[:30]:
        print(f"      - {s['title']}")
    if len(summer_subs) > 30:
        print(f"      ... +{len(summer_subs) - 30} more")

    print("\n[B] Walk Winter Olympics competitors for the US:")
    winter_subs = cat_members("Winter_Olympics_competitors_for_the_United_States", cmtype="subcat")
    print(f"    {len(winter_subs)} subcats. Sample (first 20):")
    for s in winter_subs[:20]:
        print(f"      - {s['title']}")
    if len(winter_subs) > 20:
        print(f"      ... +{len(winter_subs) - 20} more")

    print("\n[C] Pick a sport subcat and pull athletes:")
    target = None
    for s in summer_subs:
        title = s["title"].replace("Category:", "")
        if "swimmers" in title.lower() or "track" in title.lower():
            target = title
            break
    if not target and summer_subs:
        target = summer_subs[0]["title"].replace("Category:", "")
    print(f"    Using: {target}")
    pages = cat_members(target, cmtype="page")
    print(f"    -> {len(pages)} athlete pages in this category")

    print("\n[D] Extract birthplace from infobox for sample athletes (first 20):")
    sample_titles = [p["title"] for p in pages[:20]]
    wikitext = fetch_wikitext(sample_titles)
    extracted = []
    for t in sample_titles:
        wt = wikitext.get(t, "")
        bp = extract_birthplace(wt) if wt else None
        extracted.append({"title": t, "birthplace": bp})
        print(f"    {t[:40]:40s} -> {bp}")

    n_with_bp = sum(1 for r in extracted if r["birthplace"])
    print(f"\n    Coverage: {n_with_bp}/{len(extracted)} have a parseable birthplace = {100 * n_with_bp / len(extracted):.0f}%")

    print("\n[E] Try the Paralympic side too — Paralympic_swimmers_for_the_United_States, sample 10:")
    para_pages = cat_members("Paralympic_swimmers_for_the_United_States", cmtype="page")
    para_titles = [p["title"] for p in para_pages[:10]]
    para_wikitext = fetch_wikitext(para_titles)
    n_para_bp = 0
    for t in para_titles:
        bp = extract_birthplace(para_wikitext.get(t, ""))
        if bp:
            n_para_bp += 1
        print(f"    {t[:40]:40s} -> {bp}")
    print(f"    Paralympic coverage: {n_para_bp}/{len(para_titles)} = {100 * n_para_bp / max(1, len(para_titles)):.0f}%")

    print("\nVERDICT:")
    if n_with_bp >= len(extracted) * 0.6 and n_para_bp >= len(para_titles) * 0.6:
        print("  PASS -> Wikipedia category-walk + infobox extraction is viable.")
        print("  Plan Day 2: walk all Olympic + Paralympic US sport subcats, batch-fetch wikitext,")
        print("  extract birthplaces, normalize to (city, state) via geocoding.")
    else:
        print("  PARTIAL -> Birthplace coverage is uneven. Need geocoder fallback or a Kaggle complement.")

    out = {
        "summer_olympic_subcats": len(summer_subs),
        "winter_olympic_subcats": len(winter_subs),
        "sample_olympic_target": target,
        "sample_olympic_size": len(pages),
        "olympic_birthplace_coverage": f"{n_with_bp}/{len(extracted)}",
        "paralympic_birthplace_coverage": f"{n_para_bp}/{len(para_titles)}",
        "olympic_sample": extracted,
    }
    import pathlib
    pathlib.Path(__file__).parent.joinpath("wikipedia_v2_findings.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
