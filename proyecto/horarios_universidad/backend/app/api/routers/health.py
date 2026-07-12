"""Health-check endpoint (no auth, no prefix)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas.base import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[dict])
async def health_check() -> ApiResponse[dict]:
    return ApiResponse(
        message="Service is healthy",
        data={"status": "ok"},
    )
