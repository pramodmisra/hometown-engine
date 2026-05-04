"""Conversational agent endpoint. Multi-turn, grounded in aggregate BigQuery data."""
from __future__ import annotations

import json
import logging
import re
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from app.config import settings
from app.services import bigquery_client
from app.services.gemini import _check_compliance

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "agent.txt"

_SESSIONS: dict[str, list[dict]] = {}
_MAX_TURNS = 8
_MAX_SESSIONS = 200


class AgentMessage(BaseModel):
    role: str = Field(..., pattern="^(user|model)$")
    content: str


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class AgentResponse(BaseModel):
    answer: str
    session_id: str
    turns_in_session: int
    compliance_passed: bool
    compliance_violations: list[str]


@lru_cache(maxsize=1)
def _aggregate_summary() -> str:
    rows = bigquery_client.query_all_states_summary()
    detail_rows = _detail_rows()
    bundled = {
        "per_state_totals": rows,
        "top_per_state_sports": detail_rows,
        "note": "Aggregate counts only. No individual athlete records exist.",
    }
    return json.dumps(bundled, indent=1, ensure_ascii=False)


def _detail_rows() -> list[dict]:
    sql = f"""
    WITH ranked AS (
      SELECT state_code, region_name AS state, sport, is_paralympic, athlete_count,
        ROW_NUMBER() OVER (PARTITION BY state_code, is_paralympic ORDER BY athlete_count DESC) AS rk
      FROM `{settings.gcp_project}.{settings.bq_dataset}.athletes_aggregate`
    )
    SELECT state_code, state, sport, is_paralympic, athlete_count
    FROM ranked
    WHERE rk <= 8
    ORDER BY state_code, is_paralympic, athlete_count DESC
    """
    job = bigquery_client.get_client().query(sql, location=settings.bq_location)
    return [
        {
            "state_code": r["state_code"],
            "state": r["state"],
            "sport": r["sport"],
            "is_paralympic": bool(r["is_paralympic"]),
            "athlete_count": int(r["athlete_count"]),
        }
        for r in job.result()
    ]


@lru_cache(maxsize=1)
def _gemini_client() -> genai.Client:
    return genai.Client(vertexai=True, project=settings.gcp_project, location=settings.vertex_location)


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(no prior turns)"
    return "\n".join(f"{m['role']}: {m['content']}" for m in history[-_MAX_TURNS:])


_NAME_LIKE_PATTERN = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")

# Sport names, place names, and program names that look like 'Firstname Lastname'
# but are NOT athlete names. Loaded once and used to skip the redactor.
_ALLOW_NAME_PHRASES = {
    # US states & territories that are 2 capitalized words
    "New York", "New Jersey", "New Hampshire", "New Mexico",
    "North Carolina", "North Dakota", "South Carolina", "South Dakota",
    "Rhode Island", "West Virginia", "Puerto Rico", "American Samoa",
    "United States", "District Of Columbia",
    # known venues
    "Lake Placid", "Park City", "Salt Lake", "Long Beach",
    "Chula Vista", "Colorado Springs", "Hayward Field",
    # team / program brands
    "Team USA", "Olympic Games", "Paralympic Games",
    # Olympic / Paralympic sport labels (Olympic side)
    "Alpine Skiing", "Cross-Country Skiing", "Cross Country", "Field Hockey",
    "Figure Skating", "Ice Hockey", "Modern Pentathlon", "Real Tennis",
    "Speed Skating", "Sport Climbing", "Tug Of War", "Beach Volleyball",
    "Water Polo", "Artistic Swimming", "Table Tennis", "Nordic Combined",
    "Ski Jumping", "Ski Mountaineering", "Sled Dog Racing", "Track And Field",
    "Short Track", "Ice Skating",
    # Paralympic sport labels
    "Para Alpine", "Para Archery", "Para Athletics", "Para Badminton",
    "Para Biathlon", "Para Canoe", "Para Cross-Country", "Para Cycling",
    "Para Equestrian", "Para Football", "Para Ice", "Para Judo",
    "Para Powerlifting", "Para Rowing", "Para Sailing", "Para Shooting",
    "Para Snowboarding", "Para Swimming", "Para Table", "Para Taekwondo",
    "Para Triathlon", "Para Wrestling", "Wheelchair Basketball",
    "Wheelchair Curling", "Wheelchair Fencing", "Wheelchair Rugby",
    "Wheelchair Tennis", "Sitting Volleyball",
}


_ALLOW_LOWER = {p.lower() for p in _ALLOW_NAME_PHRASES}


_NON_NAME_PREFIXES = (
    "para ", "wheelchair ", "sitting ", "olympic ", "paralympic ", "team ", "north ",
    "south ", "east ", "west ", "new ", "old ", "great ", "winter ", "summer ",
    "adaptive ", "other ", "many ", "while ", "their ", "across ", "within ",
    "the ", "this ", "these ", "those ", "for ", "in ", "on ", "with ", "without ",
    "men's ", "women's ", "national ", "international ", "world ", "global ",
    # second halves of hyphenated sport names that the regex catches when split
    "country ",  # from "Cross-Country Skiing"
    "track ",    # from "Short-Track Speed Skating"
    "field ",    # from "Track and Field"
)


def _strip_athlete_names(text: str) -> str:
    """Defense-in-depth: replace plausible 'Firstname Lastname' tokens not in the allowlist.
    Allowlist includes US states, venues, Olympic/Paralympic sport names, and common
    non-name two-word phrases starting with prefixes like 'Olympic', 'Para', 'Team'."""
    def repl(m: re.Match) -> str:
        phrase = m.group(0)
        low = phrase.lower()
        if low in _ALLOW_LOWER:
            return phrase
        if low.startswith(_NON_NAME_PREFIXES):
            return phrase
        return "[athlete name redacted]"
    return _NAME_LIKE_PATTERN.sub(repl, text)


def _evict_session_if_needed() -> None:
    if len(_SESSIONS) > _MAX_SESSIONS:
        oldest = next(iter(_SESSIONS))
        _SESSIONS.pop(oldest, None)


@router.post("/ask", response_model=AgentResponse)
def ask(request: AgentRequest) -> AgentResponse:
    sid = request.session_id or str(uuid.uuid4())
    history = _SESSIONS.get(sid, [])

    template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        template
        .replace("{aggregate_summary_json}", _aggregate_summary())
        .replace("{history_text}", _format_history(history))
        .replace("{user_message}", request.message)
    )

    try:
        resp = _gemini_client().models.generate_content(
            model=settings.gemini_model_flash,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=900,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
    except Exception as e:
        log.error("Gemini call failed: %s", e)
        raise HTTPException(status_code=502, detail="agent backend unavailable") from e

    raw = (resp.text or "").strip()
    safe = _strip_athlete_names(raw)
    compliance_ok, violations = _check_compliance(safe)

    history.extend([
        {"role": "user", "content": request.message},
        {"role": "model", "content": safe},
    ])
    _SESSIONS[sid] = history[-(_MAX_TURNS * 2):]
    _evict_session_if_needed()

    return AgentResponse(
        answer=safe,
        session_id=sid,
        turns_in_session=len(_SESSIONS[sid]) // 2,
        compliance_passed=compliance_ok,
        compliance_violations=violations,
    )
