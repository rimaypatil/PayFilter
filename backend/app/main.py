"""PayFilter FastAPI Application Entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.risk_engine.model import get_model_manager
from backend.app.risk_engine.timeout_handler import get_timeout_handler
from backend.app.routes import (
    audit,
    confirmations,
    health,
    kill_switch,
    merchants,
    rules,
    transactions,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payfilter.app")

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler enforcing startup model integrity checks and background workers."""
    settings = get_settings()
    logger.info("Initializing PayFilter Backend (Phase 3 with Supabase Auth & RBAC)...")

    # 1. Load and strictly verify ML model integrity on startup
    model_mgr = get_model_manager(
        model_path=settings.MODEL_PATH,
        metadata_path=settings.MODEL_METADATA_PATH,
    )
    model_mgr.initialize()
    logger.info(f"Model integrity verified: v{model_mgr.model_version}.")

    # 2. Background scheduler (when explicitly enabled)
    scheduler = None
    if settings.ENABLE_BACKGROUND_TIMEOUT_WORKER:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler = BackgroundScheduler()
            timeout_handler = get_timeout_handler()
            scheduler.add_job(
                timeout_handler.process_held_timeouts,
                "interval",
                seconds=30,
                id="held_timeout_resolver",
            )
            scheduler.start()
            logger.info("Background timeout auto-resolution scheduler started (30s interval).")
        except Exception as e:
            logger.debug(f"APScheduler background worker skipped: {e}")

    logger.info("PayFilter Backend ready to serve requests.")
    yield

    # Shutdown
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background timeout scheduler shut down.")
    logger.info("PayFilter Backend shutting down.")


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    app = FastAPI(
        title="PayFilter Risk Engine & Auth Platform",
        description="AI Agent Transaction Risk Assessment, Supabase Auth RBAC, Human Confirmation & Kill Switch",
        version="3.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Route Handlers
    app.include_router(health.router)
    app.include_router(merchants.router)
    app.include_router(transactions.router)
    app.include_router(confirmations.router)
    app.include_router(kill_switch.router)
    app.include_router(rules.router)
    app.include_router(audit.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )
