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


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    return genai.Client(vertexai=True, project=settings.gcp_project, location=settings.vertex_location)


def _load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def _check_compliance(text: str) -> tuple[bool, list[str]]:
    violations = []
    for pattern in DISALLOWED_PATTERNS:
        m = pattern.search(text)
        if m:
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
