"""REST endpoints for institution, campus, and academic-period entities."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_uow
from app.api.schemas.base import ApiResponse
from app.api.schemas.institution import (
    AcademicPeriodCreate,
    AcademicPeriodOut,
    CampusOut,
    InstitutionCreate,
    InstitutionOut,
    InstitutionUpdate,
)
from app.application.commands.institution_commands import (
    CreateAcademicPeriod,
    CreateInstitution,
    DeleteInstitution,
    UpdateInstitution,
)
from app.application.queries.institution_queries import (
    GetActiveAcademicPeriod,
    GetInstitution,
    ListAcademicPeriods,
    ListCampuses,
    ListInstitutions,
)
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["institutions"], dependencies=[Depends(get_current_user)])


# ── Institution ──────────────────────────────────────────────────────────────


@router.post("/institutions", response_model=ApiResponse[InstitutionOut], status_code=201)
async def create_institution(
    body: InstitutionCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstitutionOut]:
    entity = CreateInstitution(uow).execute(body)
    return ApiResponse(data=InstitutionOut(**entity.__dict__), message="Institution created")


@router.get("/institutions", response_model=ApiResponse[list[InstitutionOut]])
async def list_institutions(
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[InstitutionOut]]:
    entities = ListInstitutions(uow).execute()
    return ApiResponse(
        data=[InstitutionOut(**e.__dict__) for e in entities],
        message="Institutions retrieved",
    )


@router.get("/institutions/{institution_id}", response_model=ApiResponse[InstitutionOut])
async def get_institution(
    institution_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstitutionOut]:
    entity = GetInstitution(uow).execute(institution_id)
    return ApiResponse(data=InstitutionOut(**entity.__dict__), message="Institution retrieved")


@router.put("/institutions/{institution_id}", response_model=ApiResponse[InstitutionOut])
async def update_institution(
    institution_id: UUID,
    body: InstitutionUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstitutionOut]:
    entity = UpdateInstitution(uow).execute(institution_id, body)
    return ApiResponse(data=InstitutionOut(**entity.__dict__), message="Institution updated")


@router.delete("/institutions/{institution_id}", status_code=204)
async def delete_institution(
    institution_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    DeleteInstitution(uow).execute(institution_id)
    return Response(status_code=204)


# ── Campus ───────────────────────────────────────────────────────────────────
# Only listing is exposed — campuses are seeded once per institution and
# aren't managed from the UI at all yet, so create/get/update stayed dead
# code until there's an actual campus-management screen to wire them to.


@router.get(
    "/institutions/{institution_id}/campuses",
    response_model=ApiResponse[list[CampusOut]],
)
async def list_campuses(
    institution_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[CampusOut]]:
    entities = ListCampuses(uow).execute(institution_id)
    return ApiResponse(
        data=[CampusOut(**e.__dict__) for e in entities],
        message="Campuses retrieved",
    )


# ── Academic Period ──────────────────────────────────────────────────────────


@router.post(
    "/institutions/{institution_id}/periods",
    response_model=ApiResponse[AcademicPeriodOut],
    status_code=201,
)
async def create_academic_period(
    institution_id: UUID,
    body: AcademicPeriodCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AcademicPeriodOut]:
    body.institution_id = institution_id
    entity = CreateAcademicPeriod(uow).execute(body)
    return ApiResponse(data=AcademicPeriodOut(**entity.__dict__), message="Academic period created")


@router.get(
    "/institutions/{institution_id}/periods",
    response_model=ApiResponse[list[AcademicPeriodOut]],
)
async def list_academic_periods(
    institution_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[AcademicPeriodOut]]:
    entities = ListAcademicPeriods(uow).execute(institution_id)
    return ApiResponse(
        data=[AcademicPeriodOut(**e.__dict__) for e in entities],
        message="Academic periods retrieved",
    )


@router.get(
    "/institutions/{institution_id}/periods/active",
    response_model=ApiResponse[AcademicPeriodOut],
)
async def get_active_academic_period(
    institution_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AcademicPeriodOut]:
    entity = GetActiveAcademicPeriod(uow).execute(institution_id)
    return ApiResponse(data=AcademicPeriodOut(**entity.__dict__), message="Active period retrieved")
