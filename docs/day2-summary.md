# Day 2 Summary — Data Pipeline Live + Backend Skeleton

**Date:** 2026-05-04
**Status:** Day 2 goals exceeded. Aggregate dataset, climate, regions all loaded into BigQuery. FastAPI backend skeleton built and Gemini narrative roundtrip verified end-to-end.

---

## What shipped

### Data pipeline

- **Wikipedia scraper** (`data/scrapers/wikipedia_team_usa.py`) walks 94 sport sub-categories under three Team USA roots (Summer Olympics, Winter Olympics, Paralympics) with depth-2 recursion. Filters to `ns=0`, batch-fetches wikitext (50/req), extracts `birth_place`, `hometown`, `birth_date` from infobox. Per-sport JSONL caches make the scrape resumable.
- **Aggregator** (`data/pipelines/aggregate.py`) parses raw birthplaces with a 56-state lookup, drops non-US, dedupes by `(page_id, sport, is_paralympic)`, normalizes sport names through a 90+ entry canonical map (Olympic + Paralympic), and writes Parquet + CSV.
- **BigQuery loader** (`data/pipelines/bq_load.py`) creates the `hometown_engine` dataset in US multi-region, applies the schema from `data/schemas/athletes_aggregate.sql`, and loads 1,398 aggregate rows.
- **Climate table** (`data/pipelines/bq_climate.py`) derives state-level temp + precipitation normals from `bigquery-public-data.noaa_gsod` over a 30-year window (1990-2019). 51 state rows.
- **Regions table** (`data/pipelines/bq_regions.py`) builds geometry centroids + population from `bigquery-public-data.geo_us_boundaries.states` + `census_bureau_acs.state_2020_5yr`. 56 entities (50 states + DC + 5 territories).

### Validation

10/10 known-hub expectations pass at realistic thresholds:

| State | Lens | Count | Context |
|---|---|---|---|
| Oregon | Athletics | 23 | Eugene/Hayward Field |
| California | Swimming | 66 | Stanford/UCLA/UCSB |
| Colorado | Cross-Country Skiing | 14 | Vail/Steamboat |
| Utah | Alpine Skiing | 7 | Park City |
| New York | Figure Skating | 9 | Lake Placid |
| New York | Bobsleigh | 32 | Lake Placid track |
| Minnesota | Ice Hockey | 73 | hockey culture |
| Texas | Athletics | 61 | track and field powerhouse |
| California | Para Athletics | 13 | Chula Vista training center |
| Illinois | Para Athletics | 3 | Champaign-Urbana adaptive sports |

### Backend

- FastAPI scaffold under `backend/app/`
- `/api/regions/{state_code}` returns region metadata + climate + Olympic/Paralympic athlete summary
- `/api/regions/{state_code}/narrative` calls Gemini with a why-engine prompt, returns a 1.5-2 KB conditional-phrasing narrative with 24h LRU cache
- `/api/regions` returns per-state Olympic + Paralympic totals (drives map view)
- Compliance regex filter on Gemini output (catches "produces", "guarantees", "former Olympian", etc.)
- Smoke test passed: Georgia returned **52 Olympic + 8 Paralympic athletes**, narrative was **1,688 chars, compliance-clean**, Olympic/Paralympic equal treatment confirmed.

---

## Numbers

| | First scrape | Final (depth-2) |
|---|---|---|
| Total Wikipedia pages scraped | 7,443 | 8,261 |
| With birthplace (raw) | 5,807 (78%) | 6,359 (77%) |
| US-resolved unique athletes | 5,069 | 5,567 |
| Aggregate rows in BigQuery | 1,372 | 1,398 |
| States represented | 54 | 54 |
| Distinct Olympic sports | 63 | 64 |
| Distinct Paralympic sports | 28 | 28 |
| Olympic athletes total | 4,801 | 5,239 |
| Paralympic athletes total | 268 | 328 |

---

## Known data gaps (acknowledge in product UI)

1. **Basketball / Volleyball / Baseball undercount.** Wikipedia categorizes major team sports under "Basketball at the [year] Summer Olympics" rather than "Olympic basketball players for the United States". Recursion at depth-2 from the Team USA root does not reach those by-Games-year buckets. Day 3 task: add a manual scrape pass over those buckets and merge.
2. **Florida Swimming undercount.** Wikipedia birthplace is birth-state, not training-state. Many Florida swimmers were born elsewhere. Day 3 task: incorporate `hometown=` field as a secondary signal.
3. **Climate precipitation undercount (~24%).** NOAA GSOD station-day records have systemic missing-day handling that biases annual sums low. Acceptable for relative comparisons in Gemini narratives, but document the caveat in UI.

---

## Decisions

- **BigQuery dataset location: US multi-region.** Cross-region joins to `bigquery-public-data` (which is US multi-region) require this. Vertex AI / Gemini lives in `us-central1` separately — the cross-region cost is negligible.
- **Service account scope:** `aiplatform.user`, `bigquery.dataEditor`, `bigquery.jobUser`, `bigquery.readSessionUser`, `run.admin`, `cloudbuild.builds.editor`, `storage.admin`, `iam.serviceAccountUser`, `secretmanager.secretAccessor`, `artifactregistry.writer`. Key file is gitignored at `.secrets/hometown-engine-sa.json`.
- **Gemini config:** model defaults to `gemini-2.5-flash` (fast, cheap), thinking_budget=0 (predictable token use), max_output_tokens=2000. Pro reserved for Discovery Mode / agent.
- **NIL boundary:** athlete names exist only in `data/raw/*.jsonl` (gitignored). All committed artifacts and BigQuery tables are state-grain aggregates only.

---

## Day 3 plan

1. Patch the basketball/volleyball/baseball gap with a manual by-Games-year scrape pass.
2. Add `hometown=` field as secondary signal in aggregator (improve Florida and other late-career hubs).
3. Build the Discovery Mode prompt + offline pre-compute (`/api/hubs/discover`).
4. Build the conversational agent endpoint (`/api/agent/ask`) — multi-turn with grounded BQ citations.
5. Containerize backend, deploy to Cloud Run, smoke-test the public URL.
6. Start frontend scaffold (Vite + React + TS + Tailwind), choropleth map of state Olympic + Paralympic totals.

---

*See `data/spike/SPIKE_FINDINGS.md` for the Day 1 source-evaluation work.*
