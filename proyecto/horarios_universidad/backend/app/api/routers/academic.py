"""REST endpoints for academic-structure entities."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.dependencies.auth import get_current_user, require_role
from app.api.dependencies.database import get_uow
from app.api.schemas.academic import (
    AreaCreate,
    AreaOut,
    AreaUpdate,
    CoordinatorOut,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
)
from app.api.schemas.base import ApiResponse
from app.api.schemas.infrastructure import SubjectResourceBody, SubjectResourceOut
from app.application.commands.academic_commands import (
    CreateArea,
    CreateSubject,
    DeleteArea,
    DeleteSubject,
    UpdateArea,
    UpdateSubject,
)
from app.application.queries.academic_queries import (
    GetArea,
    GetSubject,
    ListAreas,
    ListSubjects,
)
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["academic"])


# ── Area ─────────────────────────────────────────────────────────────────────


@router.post("/areas", response_model=ApiResponse[AreaOut], status_code=201)
async def create_area(
    body: AreaCreate,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AreaOut]:
    area, coordinator = CreateArea(uow).execute(body)
    out = AreaOut(
        **area.__dict__,
        coordinator=CoordinatorOut(
            user_id=coordinator.id,
            email=coordinator.email,
            name=coordinator.name,
        ),
    )
    return ApiResponse(data=out, message="Area created")


@router.get("/institutions/{institution_id}/areas", response_model=ApiResponse[list[AreaOut]])
async def list_areas(
    institution_id: UUID,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[AreaOut]]:
    entities = ListAreas(uow).execute(institution_id)
    return ApiResponse(data=[AreaOut(**e.__dict__) for e in entities], message="Areas retrieved")


@router.get("/areas/{area_id}", response_model=ApiResponse[AreaOut])
async def get_area(
    area_id: UUID,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AreaOut]:
    entity = GetArea(uow).execute(area_id)
    return ApiResponse(data=AreaOut(**entity.__dict__), message="Area retrieved")


@router.put("/areas/{area_id}", response_model=ApiResponse[AreaOut])
async def update_area(
    area_id: UUID,
    body: AreaUpdate,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[AreaOut]:
    entity = UpdateArea(uow).execute(area_id, body)
    return ApiResponse(data=AreaOut(**entity.__dict__), message="Area updated")


@router.delete("/areas/{area_id}", status_code=204)
async def delete_area(
    area_id: UUID,
    _user=Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    DeleteArea(uow).execute(area_id)
    return Response(status_code=204)


# ── Subject ──────────────────────────────────────────────────────────────────


@router.post("/subjects", response_model=ApiResponse[SubjectOut], status_code=201)
async def create_subject(
    body: SubjectCreate,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[SubjectOut]:
    entity = CreateSubject(uow).execute(body)
    return ApiResponse(data=SubjectOut(**entity.__dict__), message="Subject created")


@router.get("/institutions/{institution_id}/subjects", response_model=ApiResponse[list[SubjectOut]])
async def list_subjects(
    institution_id: UUID,
    area_id: UUID | None = None,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[SubjectOut]]:
    entities = ListSubjects(uow).execute(institution_id, area_id=area_id)
    return ApiResponse(
        data=[SubjectOut(**e.__dict__) for e in entities],
        message="Subjects retrieved",
    )


@router.get("/subjects/{subject_id}", response_model=ApiResponse[SubjectOut])
async def get_subject(
    subject_id: UUID,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[SubjectOut]:
    entity = GetSubject(uow).execute(subject_id)
    return ApiResponse(data=SubjectOut(**entity.__dict__), message="Subject retrieved")


@router.put("/subjects/{subject_id}", response_model=ApiResponse[SubjectOut])
async def update_subject(
    subject_id: UUID,
    body: SubjectUpdate,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[SubjectOut]:
    entity = UpdateSubject(uow).execute(subject_id, body)
    return ApiResponse(data=SubjectOut(**entity.__dict__), message="Subject updated")


@router.delete("/subjects/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: UUID,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    DeleteSubject(uow).execute(subject_id)
    return Response(status_code=204)


# ── Subject resource requirements ──────────────────────────────────────────


@router.get(
    "/subjects/{subject_id}/resources",
    response_model=ApiResponse[list[SubjectResourceOut]],
)
async def list_subject_resources(
    subject_id: UUID,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[SubjectResourceOut]]:
    from app.infrastructure.persistence.models.infrastructure_models import (
        SubjectResourceRequirementModel,
    )

    with uow:
        models = (
            uow._session.query(SubjectResourceRequirementModel)
            .filter(SubjectResourceRequirementModel.subject_id == subject_id)
            .all()
        )
        items = [
            SubjectResourceOut(
                id=m.id,
                subject_id=m.subject_id,
                resource_id=m.resource_id,
                is_mandatory=m.is_mandatory,
            )
            for m in models
        ]
    return ApiResponse(data=items)


@router.post(
    "/subjects/{subject_id}/resources",
    response_model=ApiResponse[SubjectResourceOut],
    status_code=201,
)
async def add_subject_resource(
    subject_id: UUID,
    body: SubjectResourceBody,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[SubjectResourceOut]:
    from app.core.utils.types import generate_id
    from app.infrastructure.persistence.models.infrastructure_models import (
        SubjectResourceRequirementModel,
    )

    with uow:
        model = SubjectResourceRequirementModel(
            id=generate_id(),
            subject_id=subject_id,
            resource_id=body.resource_id,
            is_mandatory=body.is_mandatory,
        )
        uow._session.add(model)
        uow.commit()
        out = SubjectResourceOut(
            id=model.id,
            subject_id=model.subject_id,
            resource_id=model.resource_id,
            is_mandatory=model.is_mandatory,
        )
    return ApiResponse(data=out, message="Resource requirement added")


@router.delete("/subject-resources/{requirement_id}", status_code=204)
async def remove_subject_resource(
    requirement_id: UUID,
    _user=Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    from app.infrastructure.persistence.models.infrastructure_models import (
        SubjectResourceRequirementModel,
    )

    with uow:
        model = uow._session.get(SubjectResourceRequirementModel, requirement_id)
        if model:
            uow._session.delete(model)
            uow.commit()
    return Response(status_code=204)
