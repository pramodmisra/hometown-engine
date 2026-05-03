"""Region detail + summary endpoints."""
from __future__ import annotations

import logging
import time
from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.services import bigquery_client, gemini

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/regions", tags=["regions"])

_NARRATIVE_CACHE: dict[str, tuple[float, dict]] = {}
_NARRATIVE_TTL_S = 24 * 3600


@router.get("/{state_code}")
def get_region(state_code: str) -> dict:
    state_code = state_code.upper()
    region = bigquery_client.query_region(state_code)
    if region is None:
        raise HTTPException(status_code=404, detail=f"region not found: {state_code}")
    summary = bigquery_client.query_athlete_summary(state_code)
    return {"region": region, "athlete_summary": summary}


@router.get("/{state_code}/narrative")
def get_region_narrative(state_code: str) -> dict:
    state_code = state_code.upper()
    cached = _NARRATIVE_CACHE.get(state_code)
    if cached and (time.time() - cached[0]) < _NARRATIVE_TTL_S:
        return {**cached[1], "cache_hit": True}

    region = bigquery_client.query_region(state_code)
    if region is None:
        raise HTTPException(status_code=404, detail=f"region not found: {state_code}")
    summary = bigquery_client.query_athlete_summary(state_code)

    context = {
        "region": {
            "name": region.get("region_name"),
            "state_code": region.get("state_code"),
            "type": region.get("region_type"),
        },
        "geography": {
            "latitude": region.get("latitude"),
            "longitude": region.get("longitude"),
            "area_sq_km": region.get("area_sq_km"),
            "population": region.get("population"),
        },
        "climate": {
            "avg_temp_f": region.get("avg_temp_f"),
            "avg_diurnal_range_f": region.get("avg_diurnal_range_f"),
            "avg_annual_precip_in": region.get("avg_annual_precip_in"),
        },
        "athlete_summary": summary,
    }
    result = gemini.generate_why_narrative(context)
    payload = {"state_code": state_code, "context": context, **result}
    _NARRATIVE_CACHE[state_code] = (time.time(), payload)
    return {**payload, "cache_hit": False}


@router.get("")
def list_regions_summary() -> dict:
    """Map view: per-state Olympic + Paralympic totals."""
    return {"states": bigquery_client.query_all_states_summary()}
