"""Read-side use cases for personnel management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import (
    ResourceNotFoundError,
)
from app.application.mappers.personnel_mapper import instructor_detail_to_dict

if TYPE_CHECKING:
    from app.core.utils.types import EntityId
    from app.domain.entities.personnel import (
        Instructor,
        InstructorAvailability,
        InstructorPreference,
        InstructorSpecialty,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = [
    "GetTeacher",
    "ListTeachers",
    "GetTeacherDetail",
    "GetTeacherAvailability",
    "GetTeacherSpecialties",
    "GetTeacherPreferences",
]


class GetTeacher:
    """Retrieve a single instructor by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, instructor_id: EntityId) -> Instructor:
        with self._uow:
            entity = self._uow.instructors.get_by_id(instructor_id)
            if entity is None:
                raise ResourceNotFoundError("Instructor", instructor_id)
            return entity


class ListTeachers:
    """List all instructors for an institution."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, institution_id: EntityId) -> list[Instructor]:
        with self._uow:
            return self._uow.instructors.list_by_institution(institution_id)


class GetTeacherDetail:
    """Retrieve an instructor with contracts, specialties, and qualifications."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, instructor_id: EntityId) -> dict:
        with self._uow:
            instructor = self._uow.instructors.get_by_id(instructor_id)
            if instructor is None:
                raise ResourceNotFoundError("Instructor", instructor_id)

            contracts = self._uow.contracts.list_all()
            instructor_contracts = [
                c for c in contracts if c.instructor_id == instructor_id
            ]

            specialties = self._uow.specialties.list_by_instructor(
                instructor_id,
            )

            return instructor_detail_to_dict(
                instructor=instructor,
                contracts=instructor_contracts,
                specialties=specialties,
            )


class GetTeacherAvailability:
    """Retrieve availability slots for an instructor."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        instructor_id: EntityId,
        period_id: EntityId | None = None,
    ) -> list[InstructorAvailability]:
        with self._uow:
            return self._uow.availabilities.list_by_instructor(
                instructor_id, period_id,
            )


class GetTeacherSpecialties:
    """List subjects an instructor is qualified to teach."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, instructor_id: EntityId) -> list[InstructorSpecialty]:
        with self._uow:
            return self._uow.specialties.list_by_instructor(instructor_id)


class GetTeacherPreferences:
    """Retrieve preferences for an instructor."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        instructor_id: EntityId,
        period_id: EntityId | None = None,
    ) -> list[InstructorPreference]:
        with self._uow:
            return self._uow.preferences.list_by_instructor(
                instructor_id, period_id,
            )
