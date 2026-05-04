# Demo Video Script — Hometown Engine

**Target length:** 3:00 maximum (hard rule per hackathon rules §6).
**Format:** 1080p screen recording with optional overlay text. English narration or subtitles.
**Upload:** YouTube **unlisted** (rules §6 again).
**Compliance gate:** No real athlete imagery, no IOC/USOPC marks, no logos other than Google Cloud, no Games footage, no unlicensed music.

---

## One-line pitch

> Hometown Engine turns publicly available Team USA hometown data into an interactive map and a Gemini-powered analyst, with Olympic and Paralympic athletes presented as equals throughout.

---

## Beat sheet (with running clock)

### 0:00 → 0:12 — Hook (12 s)

| What's on screen | Voiceover |
|---|---|
| Title card on a faded US-state outline. App logo (gradient square + "Hometown Engine" wordmark). Caption: *"Built with Gemini and Google Cloud."* | "Where could Team USA come from? Hometown Engine takes publicly available data on US Olympians and Paralympians and shows you the answer for any ZIP code in America." |

**Production:** No people, no athlete images, no logos other than Google Cloud. The gradient square is the favicon — blue (Olympic) → orange (Paralympic) — visualizes the parity message immediately.

### 0:12 → 0:50 — Personalization moment (38 s)

| What's on screen | Voiceover |
|---|---|
| Live home page. Cursor moves to ZIP input. Types **30022** (Alpharetta, Georgia — hold for one beat so the typing is visible). Click "Show my hometown". Page transitions to `/region/GA`. | "Let me try my own ZIP. Thirty thousand twenty-two. That's Alpharetta, just outside Atlanta." |
| Region page renders. Camera focuses on the **Olympic 87 / Paralympic 8** equal-weight cards. | "Right away, I see Georgia has produced 87 Team USA Olympians and 8 Paralympians, drawn from public Wikipedia listings — and notice the layout: Olympic and Paralympic side by side, same fonts, same chart sizes. That's the design rule across every screen." |
| Scroll to the narrative card. Wait for it to render (this is the live Gemini call — typically 3–4 s). | "Below that, Gemini reads the structured context — climate, geography, the sport breakdown — and writes a four-paragraph explanation. Note the language: 'could foster', 'may be associated with'. Conditional throughout, because geography correlates with athletic representation but doesn't cause it." |

**Production tip:** Pre-warm the narrative cache for GA before recording so the response is fast (or accept the 3–4 s wait — it makes the live-Gemini point obvious).

### 0:50 → 1:20 — Discovery Mode (30 s)

| What's on screen | Voiceover |
|---|---|
| Click the header logo, return home. Scroll to "Surprising hubs". Highlight the five tiles. Hover one — pause on **Wisconsin / Wheelchair Basketball** (Paralympic-tagged in orange). | "Discovery Mode flips the question. We give Gemini the full state-by-state aggregate and ask it to surface five surprising hubs. By design, at least two are Paralympic. Look at this one — Wisconsin, Wheelchair Basketball, seven athletes. That's a meaningful concentration in a single Paralympic sport that wouldn't show up if we only looked at totals." |
| Click into Wisconsin → region page → scroll to Paralympic card. | "When I click in, the same equal-weight layout. Wheelchair Basketball, seven athletes. Goalball, three. The data tells a Paralympic story without us having to switch to a different tab to find it." |

### 1:20 → 1:55 — Conversational agent (35 s)

| What's on screen | Voiceover |
|---|---|
| Scroll to Chat panel. Type **"What sports does the Pacific Northwest excel at, and how does the Paralympic representation compare?"** | "There's also a conversational agent. I ask: what sports does the Pacific Northwest excel at, and how does the Paralympic representation compare?" |
| Wait for response (~3-5 s). Gemini answer renders with Olympic + Paralympic numbers per state. | "Gemini is grounded in the same aggregate that's in BigQuery — so the answer cites real numbers. Washington, 37 Olympic rowers. Three Paralympic Wheelchair Basketball athletes. Oregon, 23 Olympic athletes in Athletics, three Paralympic in Para Athletics. Conditional language throughout, no athlete names — by design." |

### 1:55 → 2:30 — Google Cloud under the hood (35 s)

| What's on screen | Voiceover |
|---|---|
| Switch to GCP console: BigQuery → `geminiliveagent-489716.hometown_engine` → run a 2-second query showing the `athletes_aggregate` table and its 1,500+ rows. | "Behind the scenes — BigQuery in the US multi-region. The aggregate has 1,500 state × sport × Olympic-or-Paralympic rows. Plus a climate table from the public NOAA dataset and a regions table from Census geo boundaries — all joined in BigQuery." |
| Switch to Vertex AI logs: show a Gemini 2.5 Flash trace from the last few seconds. | "Vertex AI for Gemini 2.5. Flash for the per-region narrative — fast, cheap, predictable. Pro for Discovery Mode, run once offline so the cards are pre-computed." |
| Switch to Cloud Run console: show the two services (`hometown-engine-api` and `hometown-engine-web`), both green. | "Two Cloud Run services. Source-deploy with `gcloud run deploy --source`. Frontend is Vite + React behind nginx; backend is FastAPI with a defense-in-depth name redactor." |

### 2:30 → 2:50 — Parity emotional peak (20 s)

| What's on screen | Voiceover |
|---|---|
| Navigate to a Para-led hub: Illinois (Champaign-Urbana adaptive sports). Show the Paralympic card with Wheelchair Basketball, Para Athletics, Goalball. | "And the parity matters. This is Illinois — home of one of the country's strongest adaptive-sports programs at the University of Illinois. The Paralympic card here gets the same treatment as Texas Athletics or California Swimming. That's the message — Olympians and Paralympians are equals in this product." |

### 2:50 → 3:00 — Close (10 s)

| What's on screen | Voiceover |
|---|---|
| Title card again. "Hometown Engine — built with Gemini and Google Cloud — Team USA × Google Cloud Vibe Code for Gold Hackathon, 2026". URL on screen: `https://hometown-engine-web-865200026782.us-central1.run.app`. Apache-2.0 badge. | "Hometown Engine — built with Gemini and Google Cloud, Apache 2.0, public on GitHub. Thanks for watching." |

---

## Pre-recording checklist

- [ ] Pre-warm narrative cache for GA, IL, WI, OR by visiting each region page once.
- [ ] Confirm Discovery Mode card for Wisconsin / Wheelchair Basketball is loading (live).
- [ ] Quit all apps showing competitor logos in the OS dock / taskbar.
- [ ] Use a clean Chrome profile with no bookmarks visible.
- [ ] Set window to 1280×800 or larger so the layout is comfortable.
- [ ] Record at 30 fps minimum, 1080p.
- [ ] No music, or a license-clean track (avoid anything Olympic-themed).
- [ ] Captions in English (auto-caption pass + manual fix).

## Compliance for the video itself

- [ ] No individual athlete names mentioned in voiceover or shown in any frame.
- [ ] No Olympic Games footage anywhere in the video.
- [ ] No IOC marks (rings, torch). No USOPC marks (stars). No Paralympic Agitos.
- [ ] No corporate brand logos in any frame except Google Cloud (which is required).
- [ ] No "Olympic Games" used as the app title.
- [ ] All sport references use canonical names (Athletics not USA Track & Field, etc.).
- [ ] All claims use conditional phrasing — never "produces", "guarantees", "predicts".
- [ ] Demo URL ends in `.run.app` (no `.com` redirect that could imply a different brand).

## Submission targets (rules §6)

| Item | Value |
|---|---|
| Hosted URL | https://hometown-engine-web-865200026782.us-central1.run.app |
| Public repo | https://github.com/pramodmisra/hometown-engine |
| License | Apache 2.0 (visible in repo About) |
| Video | YouTube unlisted, ≤ 3 min |
| Devpost challenge | Challenge 2: The Hometown Success Engine |

## Backup demo flows (if something breaks live)

1. Cold-start narrative for a state that's not yet cached — wait 4-5 s while saying "this is a live Gemini call". Convert latency into a feature.
2. Discovery Mode is static-served from a baked JSON, so even if Vertex AI is down, the discoveries render.
3. Map view never depends on Gemini — even with the AI layer offline, the map tells the parity story.

## Recording order (production efficiency)

Suggest recording in this order to minimize re-takes:

1. The static title card frames (0:00, 2:50–3:00).
2. The home page sequences (map + Discovery cards).
3. The personalization sequence (ZIP 30022 → GA region page).
4. The agent sequence (typed question + Gemini answer).
5. The GCP console sequence — record ~60s, edit down.
6. The Illinois parity moment — record last, with extra hover time on the Paralympic card.

Total raw footage budget: ~5 min. Final edit: 3:00.
