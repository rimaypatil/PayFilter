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
    SUPABASE_JWT_SECRET: str = "mock-supabase-jwt-secret-key-for-test-signature-verification-12345"
    SUPABASE_JWKS_URL: Optional[str] = None
    SUPABASE_AUDIENCE: str = "authenticated"

    # Testing keys for RLS simulation
    SUPABASE_MERCHANT_A_KEY: Optional[str] = None
    SUPABASE_MERCHANT_B_KEY: Optional[str] = None

    # Model file paths (defaults to Phase 1 ml/models location)
    MODEL_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "isolation_forest.pkl")
    MODEL_METADATA_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "model_metadata.json")

    # Timeout and Confirmation settings
    HELD_TIMEOUT_SECONDS: int = 120
    LARGE_AMOUNT_THRESHOLD: float = 25000.0
    ENABLE_BACKGROUND_TIMEOUT_WORKER: bool = False

    # Step-Up Auth settings
    STEP_UP_EXPIRY_SECONDS: int = 300

    # Razorpay Test-Mode Integration
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = "mock_razorpay_webhook_secret_12345"
    ALLOW_LIVE_KEYS: bool = False

    # Claude AI Explanation Integration
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_TIMEOUT_SECONDS: float = 5.0

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

    def validate_test_keys(self) -> None:
        """Enforces that only Razorpay test-mode keys are permitted unless explicit override."""
        if self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_ID.startswith("rzp_live_") and not self.ALLOW_LIVE_KEYS:
            raise ValueError(
                "SECURITY VIOLATION: Razorpay Live Key detected in test environment. "
                "Only test-mode keys (rzp_test_...) are permitted unless ALLOW_LIVE_KEYS=true is explicitly set."
            )


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings and validates test keys."""
    settings = Settings()
    settings.validate_test_keys()
    return settings
