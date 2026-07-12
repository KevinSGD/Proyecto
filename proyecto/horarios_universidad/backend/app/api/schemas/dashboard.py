"""Request/response schemas for the dashboard."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.base import CamelModel


class DashboardOut(CamelModel):
    """Aggregated overview for the institution dashboard."""

    total_teachers: int = 0
    total_subjects: int = 0
    total_classrooms: int = 0
    total_groups: int = 0
    active_period: dict[str, Any] | None = None
    latest_run_status: str | None = None
    latest_run_id: UUID | None = None
    occupation_pct: float | None = None
    teacher_coverage_pct: float | None = None
