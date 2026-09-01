"""Configuration and environment settings for PayFilter Backend."""

from functools import lru_cache
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase connection credentials
    SUPABASE_URL: str = "https://mock.supabase.co"
    SUPABASE_SERVICE_KEY: str = "mock-service-role-key"
    SUPABASE_ANON_KEY: str = "mock-anon-key"

    # Testing keys for RLS simulation
    SUPABASE_MERCHANT_A_KEY: Optional[str] = None
    SUPABASE_MERCHANT_B_KEY: Optional[str] = None

    # Model file paths (defaults to Phase 1 ml/models location)
    MODEL_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "isolation_forest.pkl")
    MODEL_METADATA_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "model_metadata.json")

    # Service configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings."""
    return Settings()
