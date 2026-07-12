"""Write-side use cases for academic entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import ResourceNotFoundError
from app.core.security import hash_password
from app.core.utils.types import generate_id
from app.domain.entities.academic import AcademicArea, Subject
from app.domain.entities.auth import RoleName, User, UserArea

if TYPE_CHECKING:
    from uuid import UUID

    from app.api.schemas.academic import (
        AreaCreate,
        AreaUpdate,
        SubjectCreate,
        SubjectUpdate,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork


# ── Area ─────────────────────────────────────────────────────────────────────


class CreateArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: AreaCreate) -> tuple[AcademicArea, User]:
        with self._uow:
            area = AcademicArea(
                id=generate_id(),
                institution_id=data.institution_id,
                name=data.name,
                code=data.code,
                description=data.description or "",
            )
            self._uow.academic_areas.save(area)

            role = self._uow.roles.get_by_name(RoleName.AREA_COORDINATOR.value)
            if role is None:
                raise ResourceNotFoundError(
                    "Role", RoleName.AREA_COORDINATOR.value,
                )

            coordinator = User(
                id=generate_id(),
                institution_id=data.institution_id,
                role_id=role.id,
                email=data.coordinator.email,
                name=data.coordinator.name,
                hashed_password=hash_password(data.coordinator.password),
            )
            self._uow.users.save(coordinator)

            user_area = UserArea(
                id=generate_id(),
                user_id=coordinator.id,
                area_id=area.id,
            )
            self._uow.user_areas.save(user_area)

            self._uow.commit()
            return area, coordinator


class UpdateArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, area_id: UUID, data: AreaUpdate) -> AcademicArea:
        with self._uow:
            entity = self._uow.academic_areas.get_by_id(area_id)
            if entity is None:
                raise ResourceNotFoundError("AcademicArea", area_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.academic_areas.save(entity)
            self._uow.commit()
            return entity


class DeleteArea:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, area_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.academic_areas.delete(area_id)
            if not deleted:
                raise ResourceNotFoundError("AcademicArea", area_id)
            self._uow.commit()
            return True


# ── Subject ──────────────────────────────────────────────────────────────────


class CreateSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: SubjectCreate) -> Subject:
        with self._uow:
            entity = Subject(
                id=generate_id(),
                institution_id=data.institution_id,
                code=data.code,
                name=data.name,
                credit_hours=data.credit_hours,
                weekly_hours=data.weekly_hours,
                modality_default=data.modality_default,
            )
            self._uow.subjects.save(entity)
            self._uow.commit()
            return entity


class UpdateSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, subject_id: UUID, data: SubjectUpdate) -> Subject:
        with self._uow:
            entity = self._uow.subjects.get_by_id(subject_id)
            if entity is None:
                raise ResourceNotFoundError("Subject", subject_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, field, value)
            self._uow.subjects.save(entity)
            self._uow.commit()
            return entity


class DeleteSubject:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, subject_id: UUID) -> bool:
        with self._uow:
            deleted = self._uow.subjects.delete(subject_id)
            if not deleted:
                raise ResourceNotFoundError("Subject", subject_id)
            self._uow.commit()
            return True
