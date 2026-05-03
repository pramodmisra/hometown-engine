# Day 1 Data Spike — Findings & Decision

**Date:** 2026-05-03
**Goal:** Identify a defensible, public source for aggregate `(region × sport × is_paralympic × athlete_count)` data covering Team USA Olympians AND Paralympians.

---

## Sources tried

### 1. Wikidata SPARQL — REJECTED

Probed via `query.wikidata.org/sparql`:

| Query | Result |
|---|---|
| US Olympians via `occupation = Olympic athlete (Q11338576)` | 2,384 |
| US Paralympians via `occupation = Paralympic athlete (Q14085943)` | **0** |
| US Paralympians via `participant in (P1344) -> Paralympic Games` | 0 |
| State resolution from birthplace `P131*` | 1 / 50 (2%) |
| Aggregate by state × sport (5,000 LIMIT) | Gateway timeout (504) |

**Verdict:** Olympic baseline is workable but undersized. Paralympic coverage is essentially zero. Birthplace→state hierarchy is broken in Wikidata for US places. Aggregate SPARQL queries time out at scale. Not a viable primary source.

### 2. Wikipedia Categories + Infobox extraction — ACCEPTED ✅

Probed via `en.wikipedia.org/w/api.php`. Naming pattern is `[Sport]_for_the_United_States` (NOT `American_[Sport]`).

**Olympic side**
- Root: `Summer_Olympics_competitors_for_the_United_States` → **47 sport subcategories**
- Root: `Winter_Olympics_competitors_for_the_United_States` → **17 sport subcategories**
- Spot check: `Olympic_track_and_field_athletes_for_the_United_States` → **1,308 athlete pages**

**Paralympic side**
- Root: `Paralympic_competitors_for_the_United_States` → **31 sport subcategories**
- Spot check: `Paralympic_track_and_field_athletes_for_the_United_States` → 170 pages
- Spot check: `Paralympic_swimmers_for_the_United_States` → 104 pages

**Birthplace extraction via infobox `birth_place=` field, regex on wikitext:**

| Slice | Coverage |
|---|---|
| Olympic athletes (sample 20) | 12/20 = 60% |
| Paralympic athletes (sample 10) | 6/10 = 60% |

60% coverage is workable. Of the 40% missing:
- ~10% are template/list pages (filter by `namespace=0`)
- ~10% have malformed wikitext (citation refs, nested templates)
- ~20% have no birthplace listed at all (genuinely missing)

For genuinely missing birthplaces, fallback strategies in Day 2:
- Scrape the body text for "born in" or "hometown" patterns
- Use the `hometown=` field as alternative key
- Skip the athlete if neither is available; document the gap

---

## Decision

**Primary source: Wikipedia category-walk + infobox extraction.**

- License: CC BY-SA 4.0 / GFDL — fine for derived aggregates
- Coverage: ~50 Olympic sport categories + ~31 Paralympic = ~80 categories total
- Estimated athlete page count: ~10,000–15,000
- Estimated state-resolved aggregate rows: ~3,000–5,000 unique (state × sport × is_paralympic) tuples
- Hackathon compliance: aggregate-only outputs, no NIL leakage, US-only scope
- Defensibility: every athlete is sourced from a public Wikipedia article; provenance is auditable per row

**Supplementary sources for Day 2 / Day 3:**
- **NOAA climate** — BigQuery public dataset for state/county-level climate join
- **US Census places** — geocoder for hometown → FIPS state/county resolution
- **teamusa.com current rosters** — only as fallback for athletes missing Wikipedia birthplace

---

## Issues to solve in Day 2

1. **Non-US birthplaces** — Some Team USA athletes were born abroad (e.g. Abdihakem Abdirahman → Mogadishu). Decision: keep them but flag `birthplace_country != USA` in raw data, and only aggregate at hometown/state when the place resolves to a US state. Document this explicitly in the UI source caveat.
2. **Wikitext cleanup** — Strip citation refs (`{{cite web|...}}`), broken markdown links (`[[Moberly,_Missouri`), template artifacts (`{{nowrap`).
3. **Template/list pages in categories** — Filter to `ns=0` so we don't pull `Template:Footer USA Swimming 2016`.
4. **Place-name to state normalization** — Many infobox values are like `Lubbock, Texas, U.S.A.` — parse comma-separated, take the second segment, map to state FIPS.
5. **Olympic/Paralympic dual-status** — A few athletes appear in both. Decision: keep both records, flag with two rows or a flag column.
6. **Era / decade** — Wikitext infobox has `birth_date` we can parse; era assignment from there.

---

## Day 2 plan (drives Phase 1 of `CLAUDE.md`)

1. Build `data/scrapers/wikipedia_team_usa.py`:
   - Walk all subcats under Summer/Winter Olympic + Paralympic US roots
   - Filter to `ns=0` pages
   - Batch fetch wikitext (50 per request)
   - Extract `birth_place`, `hometown`, `birth_date`
   - Persist raw to local Parquet (gitignored)
2. Build `data/pipelines/aggregate.py`:
   - Normalize place strings → (city, state) via Census geocoder OR a static state-name lookup
   - Group by `(state, sport, is_paralympic)` → counts
   - Write `athletes_aggregate.parquet` and load into BigQuery
3. Validation:
   - Cross-check 10 known hubs (Eugene OR distance running, Marin CA cycling, Colorado Springs CO multi-sport, etc.)
   - Spot-check 5 Paralympic-strong regions

Estimated Day 2 work: ~6 hours of scripting + 2 hours of validation.

---

## Compliance notes

- All probe scripts query public Wikipedia/Wikidata APIs only.
- Sample JSON outputs containing athlete names are gitignored — they exist locally for development cross-checks but never enter the public repo.
- Aggregated outputs (state/sport/count) are the only records that move past the ingestion layer.
