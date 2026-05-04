# Devpost Submission Text — Hometown Engine

**Challenge:** Challenge 2 — The Hometown Success Engine
**Project URL:** https://hometown-engine-web-865200026782.us-central1.run.app
**Repository:** https://github.com/pramodmisra/hometown-engine (Apache 2.0)
**Demo video:** [unlisted YouTube link to be added before submission]

---

## Inspiration

Fans love their hometowns and they love Team USA. But the way most fan tools work, the two are disconnected — you cheer for an athlete on TV without knowing whether your zip code has helped foster anyone like them. Challenge 2 asked us to use geography to surface hubs of athletic representation, with Olympic and Paralympic athletes treated as equals throughout. We wanted to build the simplest, most personal way to answer the question: *where could Team USA come from in your part of America?*

## What it does

Hometown Engine takes publicly available aggregate data on US Olympians and Paralympians and lets a fan explore it in three ways:

1. **Personalized hometown lookup.** Enter a US ZIP code and the app routes to your state's detail page, showing how many Olympians and Paralympians the data attributes to your state, the sports cluster around that representation, and a Gemini-generated narrative explaining what local conditions could help foster that profile.
2. **Discovery Mode.** Gemini 2.5 Pro reads the entire 1,500-row aggregate and surfaces five surprising hubs — places where the data shows an unexpected concentration of athletes in a specific sport. By design, at least two surprises are Paralympic-focused.
3. **Conversational analyst.** A multi-turn agent answers open-ended questions about hubs, regional comparisons, or the Paralympic landscape — grounded in the same BigQuery aggregate, with Olympic and Paralympic given equal analytical depth in every answer.

Across every screen, Olympic and Paralympic representation share equal visual weight — same fonts, same chart sizes, same prominence — and every piece of language uses conditional phrasing ("could help foster", "may be associated with") because geography correlates with athletic representation, it does not cause athletic outcomes.

## How we built it

The data layer lives in a new `hometown_engine` BigQuery dataset in the US multi-region. Three tables: `athletes_aggregate` (1,501 rows of state × sport × Olympic-or-Paralympic counts derived from public Wikipedia category listings of US Olympians and US Paralympians), `climate` (state-level temperature, diurnal range, and precipitation normals derived from `bigquery-public-data.noaa_gsod` over 1990-2019), and `regions` (state geometry centroids, FIPS codes, and population from `bigquery-public-data.geo_us_boundaries.states` plus `census_bureau_acs.state_2020_5yr`). The aggregator is aggressive about US-scope filtering: every birthplace string is matched against a 56-name US state lookup, with anything resolving outside the US dropped before counts hit BigQuery.

Gemini sits at the center of every AI feature, all running on Vertex AI:
- `gemini-2.5-flash` writes per-region narratives. The system prompt forbids causal language with an explicit list of disallowed words, requires equal Olympic and Paralympic depth, and bans individual athlete names. Output is run through a regex compliance filter before reaching the user.
- `gemini-2.5-pro` runs Discovery Mode once offline, reading the full aggregate and identifying five surprising hubs with a hard rule of at least two Paralympic surprises. The output is cached as a static JSON and served by the API instantly.
- `gemini-2.5-flash` powers the conversational agent, grounded in a context blob of the entire aggregate plus the user's question and short conversation history. A defense-in-depth name redactor catches any "Firstname Lastname" pattern not in an allowlist of US states, venues, and Olympic/Paralympic sport names.

The frontend is React 18 + Vite + TypeScript with Tailwind, deployed to Cloud Run behind nginx. The map is `react-simple-maps` over `us-atlas` topojson, with Olympic / Paralympic / Combined toggles. The backend is FastAPI on Cloud Run. Both services source-deploy via `gcloud run deploy --source`, with the runtime authenticating to BigQuery and Vertex AI via a project service account.

## Findings

The aggregate confirms several intuitive hubs (California swimming, Minnesota ice hockey, Vermont cross-country skiing, Texas track and field) but Discovery Mode also surfaces patterns we did not expect: Wisconsin's wheelchair basketball concentration, Michigan's goalball presence, Pennsylvania's outsized field hockey footprint relative to its population. The Paralympic-first slicing also shows that California's adaptive-sports infrastructure shows up as a leader in Para Athletics and Para Swimming with 13 and 9 athletes respectively — comparable to its Olympic profile in those same disciplines.

## What's next

A natural extension is moving from state grain to metro or county grain, which would let a fan distinguish Eugene from the rest of Oregon or Champaign-Urbana from the rest of Illinois. The pieces are in place: the `regions` table already pulls FIPS codes for US counties, and the Wikipedia birthplace strings are city-level. Adding a Census ZIP-to-county geocoder and re-aggregating would unlock that view without changing the rest of the architecture.

## Built with

Google Cloud (BigQuery, Vertex AI, Cloud Run, Cloud Build, Artifact Registry, Secret Manager), Gemini 2.5 Pro and 2.5 Flash, FastAPI, React, Vite, TypeScript, Tailwind CSS, nginx, react-simple-maps, us-atlas, BigQuery public datasets (`noaa_gsod`, `geo_us_boundaries`, `census_bureau_acs`), Wikipedia / Wikidata public listings.

## Compliance

This submission complies with all hackathon content rules. No individual athlete name, image, or likeness appears in any user-facing output (every API response is aggregate-only and a defense-in-depth redactor sits in front of the agent endpoint). No IOC or USOPC intellectual property appears in any frame. The only corporate brand referenced is Google Cloud. All language — both static UI copy and Gemini-generated text — uses conditional phrasing. Sport names use canonical Olympic terminology rather than National Governing Body names. The repository is licensed under Apache 2.0, visible at the top of the GitHub About section.
