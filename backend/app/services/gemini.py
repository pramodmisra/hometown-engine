"""Vertex AI Gemini wrapper with the Why-Engine prompt + a regex compliance filter on output."""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings

log = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

DISALLOWED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(?:produces?|guarantees?|guaranteed|predicts?|will win|certain to)\b", re.IGNORECASE),
    re.compile(r"\bformer Olympian\b", re.IGNORECASE),
    re.compile(r"\bpast Olympian\b", re.IGNORECASE),
    re.compile(r"\bformer Paralympian\b", re.IGNORECASE),
    re.compile(r"\bpast Paralympian\b", re.IGNORECASE),
]

# Refusal/negation indicators that suggest the disallowed term is being quoted to refuse,
# not asserted. e.g. "I cannot predict ..." or "I will not refer to former Olympians ...".
_NEGATION_WINDOW_RX = re.compile(
    r"\b(?:cannot|can not|can't|cant|won't|will not|do not|don't|does not|doesn't|"
    r"not\s+able|unable|refuse|never|no\s+predictions?|avoid|without|"
    r"my purpose|aggregate[- ]only|outside\s+my\s+scope)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    return genai.Client(vertexai=True, project=settings.gcp_project, location=settings.vertex_location)


def _load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def _is_in_refusal_context(text: str, match_start: int, window: int = 120) -> bool:
    """True if the matched term lies within a negation/refusal window. We look at
    the preceding `window` characters of the same sentence — if a negation marker
    is present, treat the term as quoted-for-refusal, not asserted."""
    sentence_start = max(0, match_start - window)
    chunk = text[sentence_start:match_start + 1]
    last_period = chunk.rfind(".")
    last_qmark = chunk.rfind("?")
    last_excl = chunk.rfind("!")
    boundary = max(last_period, last_qmark, last_excl)
    if boundary >= 0:
        chunk = chunk[boundary + 1:]
    return bool(_NEGATION_WINDOW_RX.search(chunk))


def _check_compliance(text: str) -> tuple[bool, list[str]]:
    violations: list[str] = []
    for pattern in DISALLOWED_PATTERNS:
        for m in pattern.finditer(text):
            if _is_in_refusal_context(text, m.start()):
                continue
            violations.append(f"matched: {m.group(0)}")
    return (len(violations) == 0, violations)


def generate_why_narrative(context: dict, model: str | None = None) -> dict:
    template = _load_prompt("why_engine.txt")
    prompt = template.replace("{context_json}", json.dumps(context, indent=2, ensure_ascii=False))
    chosen = model or settings.gemini_model_flash
    log.info("calling Gemini model=%s", chosen)
    client = get_client()
    config = types.GenerateContentConfig(
        temperature=0.5,
        top_p=0.9,
        max_output_tokens=2000,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    response = client.models.generate_content(
        model=chosen,
        contents=prompt,
        config=config,
    )
    text = response.text or ""
    ok, violations = _check_compliance(text)
    return {
        "narrative": text.strip(),
        "model": chosen,
        "compliance_passed": ok,
        "compliance_violations": violations,
    }
