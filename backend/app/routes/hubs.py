"""Discovery Mode endpoint — serves pre-computed surprise hubs from data/processed/discovery.json."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hubs", tags=["hubs"])

# Look in two places: image-baked location (backend/app/data/discovery.json),
# then fall back to the dev tree at <repo>/data/processed/discovery.json.
_BAKED = Path(__file__).resolve().parent.parent / "data" / "discovery.json"
_DEV = Path(__file__).resolve().parents[3] / "data" / "processed" / "discovery.json"


def _resolve_discovery_path() -> Path | None:
    if _BAKED.exists():
        return _BAKED
    if _DEV.exists():
        return _DEV
    return None


DISCOVERY_PATH: Path | None = _resolve_discovery_path()


@lru_cache(maxsize=1)
def _load_discoveries() -> dict | None:
    p = _resolve_discovery_path()
    if p is None:
        log.warning("discovery.json not found in baked or dev path")
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@router.get("/discover")
def discover() -> dict:
    payload = _load_discoveries()
    if payload is None:
        raise HTTPException(
            status_code=503,
            detail="Discovery Mode not built yet. Run data/pipelines/build_discovery.py.",
        )
    return payload
