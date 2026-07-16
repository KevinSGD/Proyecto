"""Dashboard REST endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_uow
from app.api.schemas.base import ApiResponse
from app.api.schemas.dashboard import DashboardOut
from app.application.queries.dashboard_queries import GetDashboard
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get(
    "/institutions/{institution_id}/dashboard",
    response_model=ApiResponse[DashboardOut],
)
async def get_dashboard(
    institution_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[DashboardOut]:
    data = GetDashboard(uow).execute(institution_id)
    return ApiResponse(
        data=DashboardOut.model_validate(data),
        message="Dashboard retrieved",
    )


@router.get(
    "/institutions/{institution_id}/periods/{period_id}/dashboard",
    response_model=ApiResponse[DashboardOut],
)
async def get_dashboard_with_period(
    institution_id: UUID,
    period_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[DashboardOut]:
    data = GetDashboard(uow).execute(institution_id, period_id)
    return ApiResponse(
        data=DashboardOut.model_validate(data),
        message="Dashboard retrieved",
    )
