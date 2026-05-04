"""FastAPI entry point for the Hometown Engine backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import agent, hubs, regions

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hometown Engine API",
        description="Aggregate Team USA hometown data and Gemini-generated narratives.",
        version="0.1.0",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "name": "Hometown Engine API",
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.get("/healthz", tags=["meta"])
    def healthz() -> dict:
        return {"status": "ok"}

    app.include_router(regions.router)
    app.include_router(hubs.router)
    app.include_router(agent.router)
    return app


app = create_app()
