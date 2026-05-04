# Hometown Engine

> **Submission for the Team USA × Google Cloud "Vibe Code for Gold" Hackathon — Challenge 2: The Hometown Success Engine.**
> **Licensed under the [Apache License 2.0](LICENSE).**

A web app that takes publicly available aggregate data on US Olympians and Paralympians and lets a fan explore *where Team USA could come from* in any part of America. Olympic and Paralympic athletes are presented with equal visual weight throughout. All language uses conditional phrasing — geography correlates with athletic representation, it does not cause athletic outcomes.

## Live

- **App:** https://hometown-engine-web-865200026782.us-central1.run.app
- **API:** https://hometown-engine-api-865200026782.us-central1.run.app

## What it does

A fan enters a US ZIP code or clicks any state, and sees:

1. **Personalized hometown lookup.** Olympic and Paralympic athlete counts for the state, sport breakdown, and a Gemini-generated narrative explaining what local conditions *could help foster* that profile.
2. **Discovery Mode.** Gemini 2.5 Pro reads the entire 1,500-row aggregate and surfaces five surprising hubs. By design, at least two are Paralympic-focused.
3. **Conversational analyst.** A multi-turn agent answers open-ended questions about hubs, regional comparisons, or the Paralympic landscape — grounded in BigQuery, with Olympic and Paralympic given equal depth in every answer.

## Olympic / Paralympic parity

Every screen, every chart, and every Gemini-generated narrative gives Olympic and Paralympic athletes equal analytical depth and equal visual weight. The Olympic and Paralympic count cards on each region page share a parallel grid layout — same fonts, same chart sizes; only hue differs (blue / orange).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + TypeScript + Tailwind CSS |
| Map | react-simple-maps + us-atlas topojson |
| Backend | FastAPI (Python 3.11) |
| AI | Google Gemini 2.5 Pro and 2.5 Flash via Vertex AI |
| Database | BigQuery (`hometown_engine` dataset, US multi-region) |
| Hosting | Cloud Run (frontend nginx + backend FastAPI) |
| CI/CD | `gcloud run deploy --source` with Cloud Build |

## Data sources

All sources are public and filtered to Team USA / US scope only:

- **Wikipedia** category listings of US Olympians and Paralympians (CC BY-SA)
- **NOAA GSOD** weather station data via `bigquery-public-data.noaa_gsod` (1990-2019 normals)
- **US Census** state geometry via `bigquery-public-data.geo_us_boundaries.states`
- **US Census ACS** state population via `bigquery-public-data.census_bureau_acs.state_2020_5yr`

**Aggregate-only.** No individual athlete names, photos, or videos appear in any user-facing output. The pipeline collapses raw scraped records to `(state × sport × is_paralympic)` aggregates before anything reaches BigQuery or the API.

## Architecture

```
                ┌──────────────────────────────────────────┐
                │  Cloud Run: hometown-engine-web (nginx)  │
                └──────────────────┬───────────────────────┘
                                   │
                                   ▼
                ┌──────────────────────────────────────────┐
                │  Cloud Run: hometown-engine-api (FastAPI) │
                │   /api/regions, /api/regions/{}/narrative │
                │   /api/hubs/discover, /api/agent/ask      │
                └────────┬───────────────────────┬─────────┘
                         │                       │
                         ▼                       ▼
            ┌────────────────────────┐  ┌─────────────────────┐
            │  Vertex AI             │  │  BigQuery (US)      │
            │  - Gemini 2.5 Pro      │  │  - athletes_aggregate│
            │  - Gemini 2.5 Flash    │  │  - climate          │
            └────────────────────────┘  │  - regions          │
                                        └─────────────────────┘
```

## Repository structure

```
hometown-engine/
├── README.md
├── LICENSE                       # Apache 2.0
├── CLAUDE.md                     # project plan + constraints
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md  # compliance checklist
├── backend/                      # FastAPI service
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/               # /api/regions, /api/hubs, /api/agent
│   │   ├── services/             # bigquery_client, gemini wrapper + filters
│   │   ├── prompts/              # why_engine.txt, discovery.txt, agent.txt
│   │   └── data/discovery.json   # baked-in pre-computed hubs
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                     # Vite + React + TS app
│   ├── src/
│   │   ├── components/           # USMap, AthleteSummary, Narrative, Chat, ...
│   │   ├── pages/                # Home, Region
│   │   └── lib/                  # api client, zip-to-state map
│   ├── Dockerfile + nginx.conf
│   └── package.json
├── data/                         # ingestion, transformation, schemas
│   ├── scrapers/                 # Wikipedia category walker
│   ├── pipelines/                # aggregate, bq_load, bq_climate, bq_regions
│   ├── schemas/                  # BigQuery DDL
│   ├── validation/               # known-hub spot checks
│   └── spike/                    # exploratory scripts + findings
├── infra/
│   ├── deploy_backend.sh
│   ├── deploy_frontend.sh
│   └── warmup_demo.sh
└── docs/
    ├── day2-summary.md
    ├── demo-script.md            # 3-minute video plan
    ├── devpost-submission.md
    └── youtube-description.md
```

## Reproducing the data pipeline

The full data pipeline is reproducible from a clone of this repo with a Google Cloud project that has BigQuery, Vertex AI, and Cloud Run enabled.

```bash
# 1. Service account credentials (judges may use their own SA)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json

# 2. Scrape Wikipedia (~10 min runtime, ~8K page reads)
python data/scrapers/wikipedia_team_usa.py
python data/scrapers/wikipedia_team_sports_patch.py

# 3. Aggregate + load to BigQuery
python data/pipelines/aggregate.py
python data/pipelines/bq_load.py
python data/pipelines/bq_climate.py
python data/pipelines/bq_regions.py

# 4. (One-time) build Discovery Mode JSON
python data/pipelines/build_discovery.py
cp data/processed/discovery.json backend/app/data/discovery.json

# 5. Validate
python data/validation/check_known_hubs.py
```

## Running the backend locally

```bash
cd backend
pip install -e .
export GOOGLE_APPLICATION_CREDENTIALS=../.secrets/hometown-engine-sa.json
python -m uvicorn app.main:app --reload --port 8765
```

## Running the frontend locally

```bash
cd frontend
npm install --legacy-peer-deps
VITE_API_BASE=http://localhost:8765 npm run dev
```

## Deploying to Cloud Run

```bash
bash infra/deploy_backend.sh
bash infra/deploy_frontend.sh
```

## Compliance

This project complies with all hackathon content rules:

- No individual athlete name, image, or likeness (NIL) in any UI output
- No IOC or USOPC intellectual property
- No corporate branding except Google Cloud
- No finish times or scoring results — placement and medal counts only
- All copy and Gemini outputs use conditional phrasing
- All AI generation runs on Google Cloud Gemini

See `.github/PULL_REQUEST_TEMPLATE.md` for the per-commit checklist and `docs/demo-script.md` for the demo-video compliance gate.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

*This is a hackathon submission — the project is not under active feature development. Issues and pull requests are welcome but may not be addressed until after the contest closes (June 16, 2026).*
