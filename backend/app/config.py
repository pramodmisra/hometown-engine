"""Configuration via environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gcp_project: str = "geminiliveagent-489716"
    bq_dataset: str = "hometown_engine"
    bq_location: str = "US"
    vertex_location: str = "us-central1"

    gemini_model_flash: str = "gemini-2.5-flash"
    gemini_model_pro: str = "gemini-2.5-pro"

    cache_ttl_hours: int = 24
    cors_origins: str = "*"

    log_level: str = "INFO"


settings = Settings()
