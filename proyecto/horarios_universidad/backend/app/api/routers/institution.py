"""REST endpoints for institution, campus, and academic-period entities."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.dependencies.database import get_uow
from app.api.schemas.base import ApiResponse
from app.api.schemas.institution import (
    AcademicPeriodCreate,
    AcademicPeriodOut,
    AcademicPeriodUpdate,
    CampusCreate,
    CampusOut,
    CampusUpdate,
    ClonePeriodRequest,
    InstitutionCreate,
    InstitutionOut,
    InstitutionUpdate,
)
from app.application.commands.institution_commands import (
    CloneAcademicPeriod,
    CreateAcademicPeriod,
    CreateCampus,
    CreateInstitution,
    DeleteInstitution,
    UpdateAcademicPeriod,
    UpdateCampus,
    UpdateInstitution,
)
from app.application.queries.institution_queries import (
    GetAcademicPeriod,
    GetActiveAcademicPeriod,
    GetCampus,
    GetInstitution,
    ListAcademicPeriods,
    ListCampuses,
    ListInstitutions,
)
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["institutions"])


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


@router.post(
    "/institutions/{institution_id}/campuses",
    response_model=ApiResponse[CampusOut],
    status_code=201,
)
async def create_campus(
    institution_id: UUID,
    body: CampusCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[CampusOut]:
    body.institution_id = institution_id
    entity = CreateCampus(uow).execute(body)
    return ApiResponse(data=CampusOut(**entity.__dict__), message="Campus created")


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


@router.get("/campuses/{campus_id}", response_model=ApiResponse[CampusOut])
async def get_campus(
    campus_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[CampusOut]:
    entity = GetCampus(uow).execute(campus_id)
    return ApiResponse(data=CampusOut(**entity.__dict__), message="Campus retrieved")


@router.put("/campuses/{campus_id}", response_model=ApiResponse[CampusOut])
async def update_campus(
    campus_id: UUID,
    body: CampusUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[CampusOut]:
    entity = UpdateCampus(uow).execute(campus_id, body)
    return ApiResponse(data=CampusOut(**entity.__dict__), message="Campus updated")


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


@router.get("/periods/{period_id}", response_model=ApiResponse[AcademicPeriodOut])
async def get_academic_period(
    period_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AcademicPeriodOut]:
    entity = GetAcademicPeriod(uow).execute(period_id)
    return ApiResponse(data=AcademicPeriodOut(**entity.__dict__), message="Academic period retrieved")


@router.put("/periods/{period_id}", response_model=ApiResponse[AcademicPeriodOut])
async def update_academic_period(
    period_id: UUID,
    body: AcademicPeriodUpdate,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AcademicPeriodOut]:
    entity = UpdateAcademicPeriod(uow).execute(period_id, body)
    return ApiResponse(data=AcademicPeriodOut(**entity.__dict__), message="Academic period updated")


@router.post("/periods/{period_id}/clone", response_model=ApiResponse[AcademicPeriodOut], status_code=201)
async def clone_academic_period(
    period_id: UUID,
    body: ClonePeriodRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AcademicPeriodOut]:
    entity = CloneAcademicPeriod(uow).execute(
        source_id=period_id,
        new_name=body.name,
        new_year=body.year,
    )
    return ApiResponse(data=AcademicPeriodOut(**entity.__dict__), message="Academic period cloned")


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
