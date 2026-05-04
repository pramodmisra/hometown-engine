"""
Discovery Mode pre-compute. Asks Gemini 2.5 Pro to identify 5 surprising Team USA hubs
from the aggregate. Run offline once; the output is served statically by /api/hubs/discover.

Output: data/processed/discovery.json
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import pandas as pd
from google import genai
from google.genai import types

PROJECT = "geminiliveagent-489716"
DATASET = "hometown_engine"
LOCATION = "US"
VERTEX_LOCATION = "us-central1"
MODEL = "gemini-2.5-pro"

DATA_DIR = Path(__file__).resolve().parent.parent
PROCESSED = DATA_DIR / "processed"
PROMPT_FILE = DATA_DIR.parent / "backend" / "app" / "prompts" / "discovery.txt"
OUT_FILE = PROCESSED / "discovery.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("discovery")

SA_KEY = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or str(
    Path(__file__).resolve().parents[2] / ".secrets" / "hometown-engine-sa.json"
)


def load_aggregate_with_populations() -> list[dict]:
    from google.cloud import bigquery
    if Path(SA_KEY).exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY
    client = bigquery.Client(project=PROJECT, location=LOCATION)

    sql = f"""
    SELECT
      a.state_code,
      a.region_name AS state,
      r.population,
      a.sport,
      a.is_paralympic,
      a.athlete_count
    FROM `{PROJECT}.{DATASET}.athletes_aggregate` a
    LEFT JOIN `{PROJECT}.{DATASET}.regions` r
      USING (state_code)
    WHERE a.athlete_count >= 2
    ORDER BY a.state_code, a.athlete_count DESC
    """
    df = client.query(sql, location=LOCATION).to_dataframe()
    log.info("loaded %d aggregate rows from BigQuery", len(df))
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "state_code": r["state_code"],
            "state": r["state"],
            "population": int(r["population"]) if pd.notna(r["population"]) else None,
            "sport": r["sport"],
            "is_paralympic": bool(r["is_paralympic"]),
            "athlete_count": int(r["athlete_count"]),
        })
    return rows


def call_gemini(rows: list[dict]) -> str:
    client = genai.Client(vertexai=True, project=PROJECT, location=VERTEX_LOCATION)
    template = PROMPT_FILE.read_text(encoding="utf-8")
    prompt = template.replace("{rows_json}", json.dumps(rows, indent=1))
    log.info("calling Gemini Pro (%d input rows, ~%d chars prompt)", len(rows), len(prompt))
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=8000,
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
        ),
    )
    return response.text or ""


_CONDITIONAL_OK = re.compile(r"\b(could|may|might|conceivably|possibly|associated with|consistent with)\b", re.IGNORECASE)
_FORBIDDEN = re.compile(r"\b(produces?|guarantees?|guaranteed|predicts?|will win|former|past)\b", re.IGNORECASE)


def validate(items: list[dict]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if len(items) < 5:
        issues.append(f"expected >= 5 surprises, got {len(items)}")
    para_count = sum(1 for it in items if it.get("is_paralympic"))
    if para_count < 2:
        issues.append(f"need >= 2 Paralympic surprises, got {para_count}")
    for i, it in enumerate(items):
        for k in ("state", "state_code", "sport", "is_paralympic", "athlete_count", "surprise_reason", "explanation"):
            if k not in it:
                issues.append(f"item {i}: missing field {k}")
        text = (it.get("explanation") or "") + " " + (it.get("surprise_reason") or "")
        if not _CONDITIONAL_OK.search(text):
            issues.append(f"item {i}: no conditional phrasing in explanation")
        if _FORBIDDEN.search(text):
            issues.append(f"item {i}: forbidden term in explanation")
    return (len(issues) == 0, issues)


def main() -> int:
    rows = load_aggregate_with_populations()
    out_text = call_gemini(rows)
    out_text = out_text.strip()

    fenced = re.search(r"```(?:json)?\s*(\[[\s\S]+\])\s*```", out_text)
    if fenced:
        out_text = fenced.group(1)

    try:
        parsed = json.loads(out_text)
    except json.JSONDecodeError as e:
        log.error("Gemini did not return valid JSON: %s", e)
        log.error("raw output[:500]: %s", out_text[:500])
        debug = PROCESSED / "discovery_debug.txt"
        debug.write_text(out_text, encoding="utf-8")
        log.error("wrote raw output -> %s", debug)
        return 1

    ok, issues = validate(parsed)
    if not ok:
        log.warning("validation issues: %s", issues)
    else:
        log.info("validation passed; %d surprises (%d Paralympic)", len(parsed),
                 sum(1 for x in parsed if x.get("is_paralympic")))

    payload = {
        "discoveries": parsed,
        "validation": {"passed": ok, "issues": issues},
        "model": MODEL,
        "input_row_count": len(rows),
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("wrote -> %s", OUT_FILE)

    log.info("\n=== DISCOVERIES ===")
    for i, d in enumerate(parsed, 1):
        kind = "Para" if d.get("is_paralympic") else "Oly "
        log.info("[%d] %s %s | %s (n=%d) — %s", i, kind, d.get("state"), d.get("sport"),
                 d.get("athlete_count", 0), d.get("surprise_reason", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
