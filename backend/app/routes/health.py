"""Service healthcheck route (GET /health)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from backend.app.risk_engine.model import MLModelManager, get_model_manager
from backend.app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check service status and verified ML model version",
)
def health_check(
    model_manager: MLModelManager = Depends(get_model_manager),
) -> HealthResponse:
    """Returns service health and loaded model version."""
    return HealthResponse(
        status="ok",
        model_version=model_manager.model_version,
        model_loaded=model_manager.is_loaded,
    )
