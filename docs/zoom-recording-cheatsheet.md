# Zoom Recording Cheat Sheet — 3-Minute Demo

**Read this end-to-end once before recording. Then put it on a second screen (or print it) and talk through it during one Zoom screen-share recording.**

Target total: **2:55** (5-second buffer under the 3:00 cap).

---

## Before you hit Record (5 minutes)

1. **Warm the cache** — open Git Bash and run:
   `bash infra/warmup_demo.sh`
   (This makes all on-camera Gemini calls render in <1s.)

2. **Open Chrome in INCOGNITO mode** (Ctrl+Shift+N) and prepare 4 tabs in this order:

   | Tab | URL |
   |---|---|
   | 1 | `https://hometown-engine-web-865200026782.us-central1.run.app` |
   | 2 | `https://hometown-engine-web-865200026782.us-central1.run.app/region/IL` |
   | 3 | `https://console.cloud.google.com/bigquery?project=geminiliveagent-489716&ws=!1m4!1m3!3m2!1sgeminiliveagent-489716!2shometown_engine` |
   | 4 | `https://github.com/pramodmisra/hometown-engine/blob/main/backend/app/services/gemini.py` |

3. **Close everything else** — no other apps, no notifications, no taskbar pinned-app logos visible (e.g. Slack, Discord). Hide the Windows taskbar if possible (Settings → Personalization → Taskbar → "Auto-hide").

4. **Start a Zoom meeting** by yourself, share Tab 1, click **Record → Record on this Computer**.

5. **Open this cheat sheet on a second monitor**, or have it side-by-side. Use your phone stopwatch to track timing.

---

## The 7 beats

### Beat 1 — 0:00 to 0:15 (15 seconds)

- **ON SCREEN:** Tab 1, the home page. Hero "Where could Team USA come from?" visible.
- **SAY:** *"This is Hometown Engine, a submission for the Team USA × Google Cloud hackathon, Challenge 2. It takes publicly available data on US Olympians and Paralympians and shows you the answer for any ZIP code in America. Built with Gemini and Google Cloud."*
- **DO:** Nothing. Just sit on the hero.
- **NEXT:** When you finish saying "Google Cloud", click into the ZIP input.

### Beat 2 — 0:15 to 0:50 (35 seconds)

- **ON SCREEN:** Type **`30022`** slowly into the ZIP box. Click "Show my hometown".
- **SAY (while typing):** *"Let me try my own ZIP — three-zero-zero-two-two. That's Alpharetta, Georgia."*
- **DO:** Page transitions to `/region/GA`. Scroll down so the Olympic 87 / Paralympic 8 cards are centered.
- **SAY (when cards visible):** *"Right away I see Georgia has produced 87 Team USA Olympians and 8 Paralympians, drawn from public Wikipedia listings. Notice the layout — Olympic and Paralympic side-by-side, same fonts, same chart sizes. That's the parity rule across every screen."*
- **DO:** Scroll down to the narrative card. It should already be there from the warmup.
- **SAY:** *"Below it, Gemini reads the structured context — climate, geography, the sport breakdown — and writes a four-paragraph explanation. The language is conditional throughout — 'could foster', 'may be associated with' — because geography correlates with athletic representation, it does not cause it."*
- **NEXT:** Click the "Hometown Engine" header logo to return home.

### Beat 3 — 0:50 to 1:20 (30 seconds)

- **ON SCREEN:** Tab 1 home page, scroll down to the "Surprising hubs" section.
- **SAY:** *"Discovery Mode flips the question. We give Gemini 2.5 Pro the entire 1,500-row aggregate and ask it to surface five surprising hubs. By design, at least two are Paralympic."*
- **DO:** Hover over the **Wisconsin / Wheelchair Basketball** card (orange Paralympic-tagged tile).
- **SAY:** *"Here — Wisconsin, Wheelchair Basketball, seven athletes. That's a meaningful concentration in a single Paralympic sport that wouldn't show up if we only looked at totals."*
- **NEXT:** Switch to Tab 2 (Illinois detail page).

### Beat 4 — 1:20 to 1:55 (35 seconds)

- **ON SCREEN:** Tab 2 — Illinois detail page. Scroll down to the chat panel.
- **DO:** Click the input, type slowly: **`What sports does the Pacific Northwest excel at, and how does the Paralympic representation compare?`**
- **SAY (while typing):** *"There's also a conversational agent. I ask: what sports does the Pacific Northwest excel at, and how does the Paralympic representation compare?"*
- **DO:** Hit Enter. Wait ~3 seconds for the response.
- **SAY (after answer renders):** *"Gemini answers grounded in the same BigQuery aggregate — Washington has 37 Olympic rowers, Oregon has 23 in Athletics, and both states show Paralympic representation. Conditional language throughout, no athlete names by design."*
- **NEXT:** Switch to Tab 3 (BigQuery console).

### Beat 5 — 1:55 to 2:30 (35 seconds)

- **ON SCREEN:** Tab 3 — BigQuery console showing the `hometown_engine` dataset.
- **DO:** Click on the `athletes_aggregate` table to show its schema/preview.
- **SAY:** *"Behind the scenes — BigQuery in the US multi-region. The aggregate has 1,500 state-by-sport-by-Olympic-or-Paralympic rows. Plus a climate table from the public NOAA dataset and a regions table from Census state geometry — all joined in BigQuery."*
- **DO:** Switch to Tab 4 — `gemini.py` source code on GitHub.
- **SAY:** *"On Vertex AI, Gemini 2.5 Flash for the per-region narratives, 2.5 Pro for Discovery Mode. The compliance regex you see here strips any forbidden language from output before it reaches the user. Both backend and frontend are on Cloud Run."*
- **NEXT:** Switch back to Tab 2 (Illinois page) — scroll to the Paralympic card.

### Beat 6 — 2:30 to 2:50 (20 seconds)

- **ON SCREEN:** Tab 2 — Illinois region page, **Paralympic card** centered.
- **SAY:** *"And the parity matters. This is Illinois — home of one of the country's strongest adaptive-sports programs at the University of Illinois. The Paralympic card here gets the same treatment as Texas Athletics or California Swimming. That's the message — Olympians and Paralympians as equals in this product."*
- **NEXT:** Scroll up to the Illinois page header so the page name is on screen for the closing.

### Beat 7 — 2:50 to 2:55 (5 seconds)

- **ON SCREEN:** Tab 2 header still visible. (No need for a separate title card.)
- **SAY:** *"Hometown Engine, built with Gemini and Google Cloud. Apache 2.0, public on GitHub. Thanks for watching."*
- **NEXT:** Stop the Zoom recording.

---

## After recording (10 minutes)

1. **Find the file:** Zoom saves to `Documents\Zoom\` by default. Look for the most recent folder, then `zoom_0.mp4`.

2. **Trim if over 3:00:** Open the MP4 in Windows **Photos app**, click "Edit & Create" → "Trim". Drag the end handle back to 2:58. Save as a copy.

3. **Upload to YouTube:**
   - Go to https://studio.youtube.com → "Upload"
   - **Visibility: UNLISTED** (rules §6 — never public, never on social media)
   - **Title:** `Hometown Engine — Team USA × Google Cloud Hackathon (Challenge 2)`
   - **Description:** copy from `docs/youtube-description.md`
   - **Audience:** "No, it's not made for kids"
   - **Captions:** YouTube will auto-generate — review for sport-name typos before submitting

4. **Submit on Devpost:** Paste the unlisted YouTube URL into the submission form. Use `docs/devpost-submission.md` for the project description. Challenge 2 selected.

---

## Quick recovery cards (if something goes wrong on camera)

| Problem | Recovery |
|---|---|
| Narrative is slow to render | Talk through climate context while it loads. The 3-4s wait is real Gemini latency — narrate it: "this is a live Gemini call, takes a few seconds." |
| Agent times out | Re-ask a simpler question: "Which states excel at swimming?" |
| BigQuery console slow to load | Have the schema view open in a backup tab — switch to it and continue |
| You go over 3:00 | Cut Beat 6 (Illinois parity moment) — say only the first sentence, stop. Beat 7 closes you at 2:50. |

---

## Compliance must-haves while recording

- [ ] No athlete name appears in any frame, voiceover, or chat answer
- [ ] No Olympic Games footage, no real athlete imagery
- [ ] No corporate logos other than Google Cloud (check Chrome extensions, taskbar, browser bookmarks)
- [ ] No IOC marks (rings/torch), no Paralympic Agitos
- [ ] All language conditional — "could", "may", "might" — never "will produce" or "guarantees"

If you nail those, the rest is icing.
