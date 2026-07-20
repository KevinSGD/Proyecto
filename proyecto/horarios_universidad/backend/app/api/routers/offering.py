"""REST endpoints for offerings, offering lines, schedule types and groups."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user, require_role
from app.api.dependencies.database import get_uow
from app.api.schemas.base import ApiResponse
from app.api.schemas.offering import (
    GroupCreate,
    GroupInstructorAssign,
    GroupOut,
    GroupUpdate,
    OfferingCreate,
    OfferingDetail,
    OfferingLineCreate,
    OfferingLineOut,
    OfferingLineUpdate,
    OfferingOut,
    OfferingRejectBody,
    OfferingUpdate,
    ScheduleTypeCreate,
    ScheduleTypeOut,
    ScheduleTypeUpdate,
    SubjectGroupCreate,
)
from app.application.commands.offering_commands import (
    AddOfferingLine,
    ApproveOffering,
    AssignGroupInstructor,
    CreateGroup,
    CreateOffering,
    CreateScheduleType,
    CreateSubjectGroup,
    DeleteGroup,
    DeleteOffering,
    DeleteScheduleType,
    GenerateGroupsFromOffering,
    RejectOffering,
    RemoveOfferingLine,
    ResubmitOffering,
    SubmitOffering,
    UpdateGroup,
    UpdateOffering,
    UpdateOfferingLine,
    UpdateScheduleType,
)
from app.application.mappers.offering_mapper import (
    group_to_dict,
    offering_detail_to_dict,
    offering_line_to_dict,
    offering_to_dict,
    schedule_type_to_dict,
)
from app.application.queries.offering_queries import (
    GetGroup,
    GetOffering,
    GetOfferingDetail,
    GetScheduleType,
    ListGroups,
    ListOfferingLines,
    ListOfferings,
    ListScheduleTypes,
)
from app.application.services.auth_service import AuthService
from app.domain.entities.auth import User
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["offerings"], dependencies=[Depends(get_current_user)])


def _ensure_subject_area_access(uow: UnitOfWork, user: User, subject_id: UUID) -> None:
    """Restrict area-coordinator users to subjects within their own area."""
    role = AuthService(uow).get_role_display_name(user)
    if role != "coordinador":
        return
    with uow:
        areas = uow.user_areas.list_by_user(user.id)
        area_id = str(areas[0].area_id) if areas else None
        subject = uow.subjects.get_by_id(subject_id)
    if subject is None or not area_id or str(subject.area_id) != area_id:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta materia",
        )


def _ensure_group_area_access(uow: UnitOfWork, user: User, group_id: UUID) -> None:
    """Restrict area-coordinator users to groups within their own area."""
    role = AuthService(uow).get_role_display_name(user)
    if role != "coordinador":
        return
    with uow:
        group = uow.groups.get_by_id(group_id)
    if group is None:
        return
    _ensure_subject_area_access(uow, user, group.subject_id)

_Uow = Depends(get_uow)


@router.post("/offerings", response_model=ApiResponse[OfferingOut])
def create_offering(body: OfferingCreate, uow: UnitOfWork = _Uow):
    entity = CreateOffering(uow).execute(body)
    return ApiResponse(message="Offering created", data=OfferingOut(**offering_to_dict(entity)))


@router.get(
    "/institutions/{inst_id}/periods/{period_id}/offerings",
    response_model=ApiResponse[list[OfferingOut]],
)
def list_offerings(inst_id: UUID, period_id: UUID, uow: UnitOfWork = _Uow):
    items = ListOfferings(uow).execute(inst_id, period_id)
    return ApiResponse(data=[OfferingOut(**offering_to_dict(o)) for o in items])


@router.get("/offerings/{offering_id}", response_model=ApiResponse[OfferingOut])
def get_offering(offering_id: UUID, uow: UnitOfWork = _Uow):
    entity = GetOffering(uow).execute(offering_id)
    return ApiResponse(data=OfferingOut(**offering_to_dict(entity)))


@router.get("/offerings/{offering_id}/detail", response_model=ApiResponse[OfferingDetail])
def get_offering_detail(offering_id: UUID, uow: UnitOfWork = _Uow):
    offering, lines = GetOfferingDetail(uow).execute(offering_id)
    return ApiResponse(data=OfferingDetail(**offering_detail_to_dict(offering, lines)))


@router.put("/offerings/{offering_id}", response_model=ApiResponse[OfferingOut])
def update_offering(offering_id: UUID, body: OfferingUpdate, uow: UnitOfWork = _Uow):
    entity = UpdateOffering(uow).execute(offering_id, body)
    return ApiResponse(message="Offering updated", data=OfferingOut(**offering_to_dict(entity)))


@router.delete("/offerings/{offering_id}", response_model=ApiResponse[bool])
def delete_offering(offering_id: UUID, uow: UnitOfWork = _Uow):
    DeleteOffering(uow).execute(offering_id)
    return ApiResponse(message="Offering deleted", data=True)


# ── Offering workflow (state machine) ──────────────────────────────────────


@router.post("/offerings/{offering_id}/submit", response_model=ApiResponse[OfferingOut])
def submit_offering(offering_id: UUID, uow: UnitOfWork = _Uow):
    entity = SubmitOffering(uow).execute(offering_id)
    return ApiResponse(message="Offering submitted", data=OfferingOut(**offering_to_dict(entity)))


@router.post(
    "/offerings/{offering_id}/approve",
    response_model=ApiResponse[OfferingOut],
    dependencies=[Depends(require_role("director"))],
)
def approve_offering(offering_id: UUID, uow: UnitOfWork = _Uow):
    entity = ApproveOffering(uow).execute(offering_id)
    return ApiResponse(message="Offering approved", data=OfferingOut(**offering_to_dict(entity)))


@router.post(
    "/offerings/{offering_id}/reject",
    response_model=ApiResponse[OfferingOut],
    dependencies=[Depends(require_role("director"))],
)
def reject_offering(offering_id: UUID, body: OfferingRejectBody, uow: UnitOfWork = _Uow):
    entity = RejectOffering(uow).execute(offering_id, body.observations)
    return ApiResponse(message="Offering rejected", data=OfferingOut(**offering_to_dict(entity)))


@router.post("/offerings/{offering_id}/resubmit", response_model=ApiResponse[OfferingOut])
def resubmit_offering(offering_id: UUID, uow: UnitOfWork = _Uow):
    entity = ResubmitOffering(uow).execute(offering_id)
    return ApiResponse(message="Offering returned to draft", data=OfferingOut(**offering_to_dict(entity)))


@router.post("/offerings/{offering_id}/lines", response_model=ApiResponse[OfferingLineOut])
def add_offering_line(offering_id: UUID, body: OfferingLineCreate, uow: UnitOfWork = _Uow):
    body.offering_id = offering_id
    entity = AddOfferingLine(uow).execute(body)
    return ApiResponse(
        message="Offering line added",
        data=OfferingLineOut(**offering_line_to_dict(entity)),
    )


@router.get(
    "/offerings/{offering_id}/lines",
    response_model=ApiResponse[list[OfferingLineOut]],
)
def list_offering_lines(offering_id: UUID, uow: UnitOfWork = _Uow):
    items = ListOfferingLines(uow).execute(offering_id)
    return ApiResponse(data=[OfferingLineOut(**offering_line_to_dict(ln)) for ln in items])


@router.put("/offering-lines/{line_id}", response_model=ApiResponse[OfferingLineOut])
def update_offering_line(line_id: UUID, body: OfferingLineUpdate, uow: UnitOfWork = _Uow):
    entity = UpdateOfferingLine(uow).execute(line_id, body)
    return ApiResponse(
        message="Offering line updated",
        data=OfferingLineOut(**offering_line_to_dict(entity)),
    )


@router.delete("/offering-lines/{line_id}", response_model=ApiResponse[bool])
def remove_offering_line(line_id: UUID, uow: UnitOfWork = _Uow):
    RemoveOfferingLine(uow).execute(line_id)
    return ApiResponse(message="Offering line removed", data=True)


@router.post(
    "/offerings/{offering_id}/generate-groups",
    response_model=ApiResponse[list[GroupOut]],
)
def generate_groups(offering_id: UUID, uow: UnitOfWork = _Uow):
    groups = GenerateGroupsFromOffering(uow).execute(offering_id)
    return ApiResponse(
        message=f"{len(groups)} group(s) generated",
        data=[GroupOut(**group_to_dict(g)) for g in groups],
    )


@router.post("/schedule-types", response_model=ApiResponse[ScheduleTypeOut])
def create_schedule_type(body: ScheduleTypeCreate, uow: UnitOfWork = _Uow):
    entity = CreateScheduleType(uow).execute(body)
    return ApiResponse(
        message="Schedule type created",
        data=ScheduleTypeOut(**schedule_type_to_dict(entity)),
    )


@router.get(
    "/institutions/{inst_id}/schedule-types",
    response_model=ApiResponse[list[ScheduleTypeOut]],
)
def list_schedule_types(inst_id: UUID, uow: UnitOfWork = _Uow):
    items = ListScheduleTypes(uow).execute(inst_id)
    return ApiResponse(data=[ScheduleTypeOut(**schedule_type_to_dict(st)) for st in items])


@router.get("/schedule-types/{st_id}", response_model=ApiResponse[ScheduleTypeOut])
def get_schedule_type(st_id: UUID, uow: UnitOfWork = _Uow):
    entity = GetScheduleType(uow).execute(st_id)
    return ApiResponse(data=ScheduleTypeOut(**schedule_type_to_dict(entity)))


@router.put("/schedule-types/{st_id}", response_model=ApiResponse[ScheduleTypeOut])
def update_schedule_type(st_id: UUID, body: ScheduleTypeUpdate, uow: UnitOfWork = _Uow):
    entity = UpdateScheduleType(uow).execute(st_id, body)
    return ApiResponse(
        message="Schedule type updated",
        data=ScheduleTypeOut(**schedule_type_to_dict(entity)),
    )


@router.delete("/schedule-types/{st_id}", response_model=ApiResponse[bool])
def delete_schedule_type(st_id: UUID, uow: UnitOfWork = _Uow):
    DeleteScheduleType(uow).execute(st_id)
    return ApiResponse(message="Schedule type deleted", data=True)


@router.get(
    "/institutions/{inst_id}/periods/{period_id}/groups",
    response_model=ApiResponse[list[GroupOut]],
)
def list_groups(inst_id: UUID, period_id: UUID, uow: UnitOfWork = _Uow):
    items = ListGroups(uow).execute(inst_id, period_id)
    return ApiResponse(data=[GroupOut(**group_to_dict(g)) for g in items])


@router.get("/groups/{group_id}", response_model=ApiResponse[GroupOut])
def get_group(group_id: UUID, uow: UnitOfWork = _Uow):
    entity = GetGroup(uow).execute(group_id)
    return ApiResponse(data=GroupOut(**group_to_dict(entity)))


@router.put("/groups/{group_id}", response_model=ApiResponse[GroupOut])
def update_group(group_id: UUID, body: GroupUpdate, uow: UnitOfWork = _Uow):
    entity = UpdateGroup(uow).execute(group_id, body)
    return ApiResponse(message="Group updated", data=GroupOut(**group_to_dict(entity)))


@router.put("/groups/{group_id}/instructor", response_model=ApiResponse[GroupOut])
def assign_group_instructor(
    group_id: UUID,
    body: GroupInstructorAssign,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    _ensure_group_area_access(uow, user, group_id)
    entity = AssignGroupInstructor(uow).execute(group_id, body.instructor_id)
    return ApiResponse(message="Group instructor updated", data=GroupOut(**group_to_dict(entity)))


@router.delete("/groups/{group_id}", response_model=ApiResponse[bool])
def delete_group(group_id: UUID, uow: UnitOfWork = _Uow):
    DeleteGroup(uow).execute(group_id)
    return ApiResponse(message="Group deleted", data=True)


# ── Subject groups (director/coordinator-facing, from the Materia form) ────


@router.get(
    "/subjects/{subject_id}/groups",
    response_model=ApiResponse[list[GroupOut]],
)
def list_subject_groups(
    subject_id: UUID,
    period_id: UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    _ensure_subject_area_access(uow, user, subject_id)
    with uow:
        subject = uow.subjects.get_by_id(subject_id)
    if subject is None:
        from app.application.exceptions.application_exceptions import (
            ResourceNotFoundError,
        )

        raise ResourceNotFoundError("Subject", subject_id)
    items = [
        g for g in ListGroups(uow).execute(subject.institution_id, period_id)
        if g.subject_id == subject_id
    ]
    return ApiResponse(data=[GroupOut(**group_to_dict(g)) for g in items])


@router.post(
    "/subjects/{subject_id}/groups",
    response_model=ApiResponse[GroupOut],
    status_code=201,
)
def create_subject_group(
    subject_id: UUID,
    body: SubjectGroupCreate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    _ensure_subject_area_access(uow, user, subject_id)
    entity = CreateSubjectGroup(uow).execute(subject_id, body)
    return ApiResponse(message="Group created", data=GroupOut(**group_to_dict(entity)))
