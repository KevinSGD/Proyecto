"""Personnel (instructor/teacher) REST endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import get_current_user, require_role
from app.api.dependencies.database import get_uow
from app.api.schemas.base import ApiResponse
from app.application.services.auth_service import AuthService
from app.domain.entities.auth import User
from app.api.schemas.personnel import (
    AvailabilityBulkSet,
    AvailabilityOut,
    ContractCreate,
    ContractOut,
    ContractUpdate,
    InstructorCreate,
    InstructorDetail,
    InstructorOut,
    InstructorUpdate,
    PreferenceCreate,
    PreferenceOut,
    SpecialtyCreate,
    SpecialtyOut,
)
from app.application.commands.personnel_commands import (
    AssignTeacherSubject,
    CreateTeacher,
    CreateTeacherContract,
    DeleteTeacher,
    RemoveTeacherSubject,
    SetTeacherAvailability,
    SetTeacherPreference,
    UpdateTeacher,
    UpdateTeacherContract,
)
from app.application.queries.personnel_queries import (
    GetTeacher,
    GetTeacherAvailability,
    GetTeacherDetail,
    GetTeacherPreferences,
    GetTeacherSpecialties,
    ListTeachers,
)
from app.domain.interfaces.unit_of_work import UnitOfWork

router = APIRouter(tags=["teachers"], dependencies=[Depends(get_current_user)])


def _current_user_area_id(uow: UnitOfWork, user_id) -> str | None:
    with uow:
        areas = uow.user_areas.list_by_user(user_id)
        return str(areas[0].area_id) if areas else None


def _ensure_area_access(uow: UnitOfWork, user: User, instructor_id: UUID) -> None:
    """Restrict area-coordinator users to instructors within their own area."""
    role = AuthService(uow).get_role_display_name(user)
    if role != "coordinador":
        return
    area_id = _current_user_area_id(uow, user.id)
    with uow:
        instructor = uow.instructors.get_by_id(instructor_id)
    if instructor is None or not area_id or str(instructor.area_id) != area_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este docente",
        )


@router.post("/teachers", response_model=ApiResponse[InstructorOut], status_code=201)
async def create_teacher(
    body: InstructorCreate,
    _user: User = Depends(require_role("director")),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstructorOut]:
    entity = CreateTeacher(uow).execute(body)
    return ApiResponse(
        data=InstructorOut.model_validate(asdict(entity)),
        message="Teacher created",
    )


@router.get("/institutions/{institution_id}/teachers", response_model=ApiResponse[list[InstructorOut]])
async def list_teachers(
    institution_id: UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[InstructorOut]]:
    entities = ListTeachers(uow).execute(institution_id)

    role = AuthService(uow).get_role_display_name(user)
    if role == "coordinador":
        area_id = _current_user_area_id(uow, user.id)
        entities = [e for e in entities if area_id and str(e.area_id) == area_id]

    with uow:
        contracts = uow.contracts.list_all()
        subjects = uow.subjects.list_by_institution(institution_id)
        specialties_by_instructor = {
            str(e.id): uow.specialties.list_by_instructor(e.id) for e in entities
        }
    contract_map: dict[str, Any] = {}
    for c in contracts:
        if c.is_active and str(c.instructor_id) not in contract_map:
            contract_map[str(c.instructor_id)] = c
    subject_hours = {str(s.id): s.weekly_hours for s in subjects}

    items = []
    for e in entities:
        d = asdict(e)
        c = contract_map.get(str(e.id))
        if c:
            d["contract_type"] = c.contract_type
            d["max_weekly_hours"] = c.max_weekly_periods
        d["assigned_hours"] = sum(
            subject_hours.get(str(sp.subject_id), 0)
            for sp in specialties_by_instructor.get(str(e.id), [])
        )
        items.append(InstructorOut.model_validate(d))
    return ApiResponse(data=items, message="Teachers retrieved")


@router.get("/teachers/{teacher_id}", response_model=ApiResponse[InstructorOut])
async def get_teacher(
    teacher_id: UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstructorOut]:
    _ensure_area_access(uow, user, teacher_id)
    entity = GetTeacher(uow).execute(teacher_id)
    return ApiResponse(
        data=InstructorOut.model_validate(asdict(entity)),
        message="Teacher retrieved",
    )


@router.get("/teachers/{teacher_id}/detail", response_model=ApiResponse[InstructorDetail])
async def get_teacher_detail(
    teacher_id: UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstructorDetail]:
    _ensure_area_access(uow, user, teacher_id)
    detail = GetTeacherDetail(uow).execute(teacher_id)
    return ApiResponse(
        data=InstructorDetail.model_validate(detail),
        message="Teacher detail retrieved",
    )


@router.put("/teachers/{teacher_id}", response_model=ApiResponse[InstructorOut])
async def update_teacher(
    teacher_id: UUID,
    body: InstructorUpdate,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[InstructorOut]:
    _ensure_area_access(uow, user, teacher_id)
    entity = UpdateTeacher(uow).execute(teacher_id, body)
    return ApiResponse(
        data=InstructorOut.model_validate(asdict(entity)),
        message="Teacher updated",
    )


@router.delete("/teachers/{teacher_id}", response_model=ApiResponse[None])
async def delete_teacher(
    teacher_id: UUID,
    user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[None]:
    _ensure_area_access(uow, user, teacher_id)
    DeleteTeacher(uow).execute(teacher_id)
    return ApiResponse(message="Teacher deleted")


@router.post("/teachers/{teacher_id}/contracts", response_model=ApiResponse[ContractOut], status_code=201)
async def create_contract(
    teacher_id: UUID, body: ContractCreate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ContractOut]:
    body.instructor_id = teacher_id
    entity = CreateTeacherContract(uow).execute(body)
    return ApiResponse(
        data=ContractOut.model_validate(asdict(entity)),
        message="Contract created",
    )


@router.put("/contracts/{contract_id}", response_model=ApiResponse[ContractOut])
async def update_contract(
    contract_id: UUID, body: ContractUpdate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[ContractOut]:
    entity = UpdateTeacherContract(uow).execute(contract_id, body)
    return ApiResponse(
        data=ContractOut.model_validate(asdict(entity)),
        message="Contract updated",
    )


@router.post("/teachers/{teacher_id}/specialties", response_model=ApiResponse[SpecialtyOut], status_code=201)
async def assign_specialty(
    teacher_id: UUID, body: SpecialtyCreate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[SpecialtyOut]:
    body.instructor_id = teacher_id
    entity = AssignTeacherSubject(uow).execute(body)
    return ApiResponse(
        data=SpecialtyOut.model_validate(asdict(entity)),
        message="Specialty assigned",
    )


@router.delete("/specialties/{specialty_id}", response_model=ApiResponse[None])
async def remove_specialty(
    specialty_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[None]:
    RemoveTeacherSubject(uow).execute(specialty_id)
    return ApiResponse(message="Specialty removed")


@router.get("/teachers/{teacher_id}/specialties", response_model=ApiResponse[list[SpecialtyOut]])
async def list_specialties(
    teacher_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[SpecialtyOut]]:
    entities = GetTeacherSpecialties(uow).execute(teacher_id)
    items = [SpecialtyOut.model_validate(asdict(e)) for e in entities]
    return ApiResponse(data=items, message="Specialties retrieved")


@router.get("/subjects/{subject_id}/specialties", response_model=ApiResponse[list[SpecialtyOut]])
async def list_subject_specialties(
    subject_id: UUID, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[SpecialtyOut]]:
    with uow:
        entities = uow.specialties.list_by_subject(subject_id)
    items = [SpecialtyOut.model_validate(asdict(e)) for e in entities]
    return ApiResponse(data=items, message="Subject specialties retrieved")


@router.put("/teachers/{teacher_id}/availability", response_model=ApiResponse[int])
async def set_availability(
    teacher_id: UUID, body: AvailabilityBulkSet, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[int]:
    body.instructor_id = teacher_id
    count = SetTeacherAvailability(uow).execute(body)
    return ApiResponse(data=count, message="Availability updated")


@router.get("/teachers/{teacher_id}/availability", response_model=ApiResponse[list[AvailabilityOut]])
async def get_availability(
    teacher_id: UUID,
    period_id: UUID | None = Query(default=None),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[AvailabilityOut]]:
    entities = GetTeacherAvailability(uow).execute(teacher_id, period_id)
    items = [AvailabilityOut.model_validate(asdict(e)) for e in entities]
    return ApiResponse(data=items, message="Availability retrieved")


@router.post("/teachers/{teacher_id}/preferences", response_model=ApiResponse[PreferenceOut], status_code=201)
async def set_preference(
    teacher_id: UUID, body: PreferenceCreate, uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[PreferenceOut]:
    body.instructor_id = teacher_id
    entity = SetTeacherPreference(uow).execute(body)
    return ApiResponse(
        data=PreferenceOut.model_validate(asdict(entity)),
        message="Preference saved",
    )


@router.get("/teachers/{teacher_id}/preferences", response_model=ApiResponse[list[PreferenceOut]])
async def get_preferences(
    teacher_id: UUID,
    period_id: UUID | None = Query(default=None),
    uow: UnitOfWork = Depends(get_uow),
) -> ApiResponse[list[PreferenceOut]]:
    entities = GetTeacherPreferences(uow).execute(teacher_id, period_id)
    items = [PreferenceOut.model_validate(asdict(e)) for e in entities]
    return ApiResponse(data=items, message="Preferences retrieved")
