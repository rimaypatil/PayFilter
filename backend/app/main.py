"""PayFilter FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.risk_engine.model import get_model_manager
from backend.app.routes import audit, health, transactions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payfilter.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler enforcing startup model integrity checks."""
    settings = get_settings()
    logger.info("Initializing PayFilter Backend...")

    # Load and strictly verify ML model integrity on startup
    # If the SHA-256 digest does not match, SecurityError is raised and service startup is aborted
    model_mgr = get_model_manager(
        model_path=settings.MODEL_PATH,
        metadata_path=settings.MODEL_METADATA_PATH,
    )
    model_mgr.initialize()

    logger.info(f"Model integrity verified: v{model_mgr.model_version}. Service ready.")
    yield
    logger.info("PayFilter Backend shutting down.")


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    app = FastAPI(
        title="PayFilter Risk Engine API",
        description="Autonomous AI Agent Payment Risk Assessment & Cryptographic Audit Trail",
        version="2.0.0",
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

    # AUTH: added in Phase 3 (JWT/API-key authentication middleware will be registered here)

    # Register Route Handlers
    app.include_router(health.router)
    app.include_router(transactions.router)
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
