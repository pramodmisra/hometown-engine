"""
Wikipedia scraper for Team USA Olympians and Paralympians.

Walks Wikipedia's curated category trees:
  - Summer_Olympics_competitors_for_the_United_States  (Summer Olympic sports)
  - Winter_Olympics_competitors_for_the_United_States  (Winter Olympic sports)
  - Paralympic_competitors_for_the_United_States       (Paralympic sports)

For each sport subcategory:
  - List article pages (ns=0)
  - Batch-fetch wikitext (50 titles per request)
  - Extract birth_place, hometown, birth_date from infobox
  - Cache as per-sport JSONL so the scrape is resumable

Outputs:
  - data/raw/cache/{slug}.jsonl  per-sport intermediates (kept for resume)
  - data/raw/athletes_us.jsonl   compiled output, one record per (athlete, sport, is_paralympic)

License: aggregates derived from Wikipedia (CC BY-SA 4.0). No NIL data is exported
beyond the data/raw/ folder, which is gitignored. Aggregates are produced downstream.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests

API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "HometownEngineHackathon/0.1 (https://github.com/pramodmisra/hometown-engine)"

DATA_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = RAW_DIR / "cache"

REQUEST_SLEEP_S = 0.4
BATCH_SIZE = 50

MAX_SUBCATS_PER_ROOT = 100
MAX_PAGES_PER_SUBCAT = 5000
MAX_BATCHES_PER_SUBCAT = 200

OLYMPIC_ROOTS: list[tuple[str, bool]] = [
    ("Summer_Olympics_competitors_for_the_United_States", False),
    ("Winter_Olympics_competitors_for_the_United_States", False),
]
PARALYMPIC_ROOTS: list[tuple[str, bool]] = [
    ("Paralympic_competitors_for_the_United_States", True),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape")


@dataclass
class AthleteRecord:
    page_title: str
    page_id: int
    sport_category: str
    is_paralympic: bool
    birthplace_raw: str | None
    hometown_raw: str | None
    birth_date_raw: str | None


def _get(params: dict) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    r = requests.get(API, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def cat_members(category: str, cmtype: str) -> list[dict]:
    """List members of a category. cmtype is 'page' (ns=0 articles) or 'subcat'."""
    out: list[dict] = []
    cont: str | None = None
    iterations = 0
    while iterations < MAX_BATCHES_PER_SUBCAT:
        iterations += 1
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "500",
            "cmtype": cmtype,
            "cmnamespace": "0" if cmtype == "page" else "14",
            "cmprop": "ids|title|type",
            "format": "json",
            "formatversion": "2",
        }
        if cont:
            params["cmcontinue"] = cont
        j = _get(params)
        out.extend(j.get("query", {}).get("categorymembers", []))
        cont = j.get("continue", {}).get("cmcontinue")
        time.sleep(REQUEST_SLEEP_S)
        if not cont:
            break
        if len(out) >= MAX_PAGES_PER_SUBCAT:
            log.warning("hit MAX_PAGES_PER_SUBCAT (%d) for %s", MAX_PAGES_PER_SUBCAT, category)
            break
    return out


def fetch_wikitext(titles: list[str]) -> dict[str, dict]:
    """Batch fetch wikitext for up to BATCH_SIZE titles. Returns {title: {pageid, wikitext}}."""
    out: dict[str, dict] = {}
    n_batches = (len(titles) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_i in range(n_batches):
        batch = titles[batch_i * BATCH_SIZE : (batch_i + 1) * BATCH_SIZE]
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": "|".join(batch),
            "format": "json",
            "formatversion": "2",
        }
        j = _get(params)
        for p in j.get("query", {}).get("pages", []):
            title = p.get("title", "")
            if "revisions" in p and p["revisions"]:
                wt = p["revisions"][0]["slots"]["main"]["content"]
                out[title] = {"pageid": p.get("pageid", 0), "wikitext": wt}
        time.sleep(REQUEST_SLEEP_S)
    return out


_INFOBOX_FIELD_RE = re.compile(r"\|\s*({field})\s*=\s*([^\n]*)", re.IGNORECASE)


def _strip_wikitext(value: str) -> str | None:
    if not value:
        return None
    s = value.strip()
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"<ref[^/]*/>", "", s)
    s = re.sub(r"\{\{cite[^}]*\}\}", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\{\{nowrap\|([^}]+)\}\}", r"\1", s, flags=re.IGNORECASE)
    s = re.sub(r"\{\{flagicon\|[^}]+\}\}", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\{\{flag\|([^|}]+)[^}]*\}\}", r"\1", s, flags=re.IGNORECASE)
    s = re.sub(r"\{\{[^}]+\}\}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,.")
    return s or None


def extract_field(wikitext: str, field_pattern: str) -> str | None:
    if not wikitext:
        return None
    rx = re.compile(rf"\|\s*({field_pattern})\s*=\s*([^\n|}}]+)", re.IGNORECASE)
    m = rx.search(wikitext)
    if not m:
        return None
    return _strip_wikitext(m.group(2))


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _normalize_sport_label(category_title: str) -> str:
    """'Olympic track and field athletes for the United States' -> 'Track and field'."""
    s = category_title.replace("Category:", "")
    s = re.sub(r"^Olympic\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^Paralympic\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+for the United States\s*$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"s$", "", s.strip()) if s.lower().endswith("s") else s.strip()
    return s.strip().capitalize() if s else "Unknown"


def discover_sport_subcats() -> list[tuple[str, str, bool]]:
    """Returns [(subcat_name_no_prefix, sport_label, is_paralympic), ...] across all roots."""
    found: list[tuple[str, str, bool]] = []
    seen: set[str] = set()
    for root, is_para in OLYMPIC_ROOTS + PARALYMPIC_ROOTS:
        log.info("discovering subcats under %s ...", root)
        subs = cat_members(root, cmtype="subcat")
        log.info("  %d subcats", len(subs))
        kept = 0
        for s in subs[:MAX_SUBCATS_PER_ROOT]:
            title = s["title"]
            low = title.lower()
            if any(skip in low for skip in (
                "medalists", "by sport", "by year", "lists of", "military",
                "by olympics", "summer olympics competitors for", "winter olympics competitors for",
            )):
                continue
            cat_name = title.replace("Category:", "")
            if cat_name in seen:
                continue
            seen.add(cat_name)
            sport = _normalize_sport_label(title)
            found.append((cat_name, sport, is_para))
            kept += 1
        log.info("  kept %d subcats from %s", kept, root)
    return found


SUBCAT_SKIP_KEYWORDS = (
    "medalists", "lists of", "competitions", "olympics by year",
    "winter olympics for the united states", "summer olympics for the united states",
)


def gather_pages_recursive(category_no_prefix: str, max_depth: int = 2) -> list[dict]:
    """Walk a sport category and its subcategories up to max_depth, collecting article pages.
    Dedupes by pageid. Skips medalist/list/year-roll-up subcategories.
    """
    seen_ids: set[int] = set()
    out: list[dict] = []
    stack: list[tuple[str, int]] = [(category_no_prefix, 0)]
    visited_cats: set[str] = set()
    iterations = 0
    MAX_ITER = 500
    while stack and iterations < MAX_ITER:
        iterations += 1
        cat, depth = stack.pop()
        if cat in visited_cats:
            continue
        visited_cats.add(cat)
        for p in cat_members(cat, cmtype="page"):
            pid = p.get("pageid", 0)
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                out.append(p)
        if depth < max_depth:
            for sc in cat_members(cat, cmtype="subcat"):
                title = sc["title"].replace("Category:", "")
                low = title.lower()
                if any(skip in low for skip in SUBCAT_SKIP_KEYWORDS):
                    continue
                stack.append((title, depth + 1))
    return out


def scrape_subcat(category_no_prefix: str, sport: str, is_paralympic: bool, force: bool = False) -> Path:
    cache_path = CACHE_DIR / f"{slugify(category_no_prefix)}.jsonl"
    if cache_path.exists() and not force:
        log.info("  cache hit -> %s", cache_path.name)
        return cache_path

    log.info("  scraping pages for %s (recursive depth=2) ...", category_no_prefix)
    pages = gather_pages_recursive(category_no_prefix, max_depth=2)
    log.info("    %d unique athlete pages found", len(pages))
    if not pages:
        cache_path.write_text("", encoding="utf-8")
        return cache_path

    titles = [p["title"] for p in pages]
    pageids_by_title = {p["title"]: p.get("pageid", 0) for p in pages}

    log.info("    fetching wikitext (%d titles, %d batches) ...", len(titles), (len(titles) + BATCH_SIZE - 1) // BATCH_SIZE)
    wt_map = fetch_wikitext(titles)
    log.info("    got wikitext for %d/%d titles", len(wt_map), len(titles))

    records: list[AthleteRecord] = []
    for title in titles:
        info = wt_map.get(title)
        wt = info["wikitext"] if info else ""
        rec = AthleteRecord(
            page_title=title,
            page_id=pageids_by_title.get(title, 0),
            sport_category=sport,
            is_paralympic=is_paralympic,
            birthplace_raw=extract_field(wt, r"birth_place|birthplace|placeofbirth"),
            hometown_raw=extract_field(wt, r"hometown|home_town|residence"),
            birth_date_raw=extract_field(wt, r"birth_date|birthdate|dateofbirth"),
        )
        records.append(rec)

    with cache_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    n_with_bp = sum(1 for r in records if r.birthplace_raw)
    log.info("    wrote %d records, %d with birthplace -> %s", len(records), n_with_bp, cache_path.name)
    return cache_path


def compile_outputs() -> Path:
    """Concatenate per-sport caches into one master JSONL."""
    out_path = RAW_DIR / "athletes_us.jsonl"
    n_total = 0
    n_with_bp = 0
    with out_path.open("w", encoding="utf-8") as out:
        for cache_file in sorted(CACHE_DIR.glob("*.jsonl")):
            for line in cache_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                out.write(line + "\n")
                n_total += 1
                rec = json.loads(line)
                if rec.get("birthplace_raw"):
                    n_with_bp += 1
    log.info("compiled %d records (%d with birthplace) -> %s", n_total, n_with_bp, out_path)
    return out_path


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="re-scrape even if cached")
    p.add_argument("--limit-subcats", type=int, default=None, help="testing: only process first N subcats")
    args = p.parse_args(argv)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("Wikipedia Team USA scraper starting")
    log.info("=" * 60)

    subcats = discover_sport_subcats()
    log.info("Total sport subcats to scrape: %d", len(subcats))
    if args.limit_subcats:
        subcats = subcats[: args.limit_subcats]
        log.info("LIMIT applied -> %d subcats", len(subcats))

    for i, (cat_name, sport, is_para) in enumerate(subcats, 1):
        prefix = "Paralympic" if is_para else "Olympic"
        log.info("[%d/%d] %s | %s | %s", i, len(subcats), prefix, sport, cat_name)
        try:
            scrape_subcat(cat_name, sport, is_para, force=args.force)
        except requests.HTTPError as e:
            log.error("  HTTP error on %s: %s -- skipping", cat_name, e)
        except Exception as e:
            log.error("  error on %s: %s -- skipping", cat_name, e)

    compile_outputs()
    log.info("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
