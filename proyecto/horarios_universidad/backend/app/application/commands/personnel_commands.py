"""Write-side use cases for personnel management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import (
    ResourceNotFoundError,
)
from app.core.utils.types import generate_id
from app.domain.entities.personnel import (
    Instructor,
    InstructorAvailability,
    InstructorContract,
    InstructorPreference,
    InstructorSpecialty,
)

if TYPE_CHECKING:
    from app.api.schemas.personnel import (
        AvailabilityBulkSet,
        ContractCreate,
        ContractUpdate,
        InstructorCreate,
        InstructorUpdate,
        PreferenceCreate,
        SpecialtyCreate,
    )
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = [
    "CreateTeacher",
    "UpdateTeacher",
    "DeleteTeacher",
    "CreateTeacherContract",
    "UpdateTeacherContract",
    "AssignTeacherSubject",
    "RemoveTeacherSubject",
    "SetTeacherAvailability",
    "SetTeacherPreference",
]


class CreateTeacher:
    """Register a new instructor."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: InstructorCreate) -> Instructor:
        with self._uow:
            entity = Instructor(
                id=generate_id(),
                institution_id=data.institution_id,
                area_id=data.area_id,
                employee_code=data.employee_code,
                first_name=data.first_name,
                last_name=data.last_name,
                email=data.email or "",
                phone=data.phone or "",
            )
            saved = self._uow.instructors.save(entity)
            self._uow.commit()
            return saved


class UpdateTeacher:
    """Update an existing instructor's fields."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, instructor_id, data: InstructorUpdate) -> Instructor:
        with self._uow:
            entity = self._uow.instructors.get_by_id(instructor_id)
            if entity is None:
                raise ResourceNotFoundError("Instructor", instructor_id)

            updates = data.model_dump(exclude_unset=True)
            for field_name, value in updates.items():
                setattr(entity, field_name, value)

            saved = self._uow.instructors.save(entity)
            self._uow.commit()
            return saved


class DeleteTeacher:
    """Remove an instructor."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, instructor_id) -> bool:
        from app.application.services.cascade_delete import delete_instructor_cascade

        with self._uow:
            existing = self._uow.instructors.get_by_id(instructor_id)
            if existing is None:
                raise ResourceNotFoundError("Instructor", instructor_id)

            delete_instructor_cascade(self._uow._session, instructor_id)
            self._uow.commit()
            return True


class CreateTeacherContract:
    """Create a contract for an instructor."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: ContractCreate) -> InstructorContract:
        with self._uow:
            entity = InstructorContract(
                id=generate_id(),
                instructor_id=data.instructor_id,
                contract_type=data.contract_type,
                start_date=data.start_date,
                end_date=data.end_date,
                max_daily_periods=data.max_daily_periods,
                max_weekly_periods=data.max_weekly_periods,
                min_weekly_periods=data.min_weekly_periods,
                max_days=data.max_days,
            )
            saved = self._uow.contracts.save(entity)
            self._uow.commit()
            return saved


class UpdateTeacherContract:
    """Update an existing instructor contract."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, contract_id, data: ContractUpdate) -> InstructorContract:
        with self._uow:
            entity = self._uow.contracts.get_by_id(contract_id)
            if entity is None:
                raise ResourceNotFoundError("InstructorContract", contract_id)

            updates = data.model_dump(exclude_unset=True)
            for field_name, value in updates.items():
                setattr(entity, field_name, value)

            saved = self._uow.contracts.save(entity)
            self._uow.commit()
            return saved


class AssignTeacherSubject:
    """Link an instructor to a subject (specialty)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: SpecialtyCreate) -> InstructorSpecialty:
        with self._uow:
            entity = InstructorSpecialty(
                id=generate_id(),
                instructor_id=data.instructor_id,
                subject_id=data.subject_id,
                proficiency_level=data.proficiency_level,
            )
            saved = self._uow.specialties.save(entity)
            self._uow.commit()
            return saved


class RemoveTeacherSubject:
    """Remove an instructor-subject link."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, specialty_id) -> bool:
        with self._uow:
            result = self._uow.specialties.delete(specialty_id)
            self._uow.commit()
            return result


class SetTeacherAvailability:
    """Bulk-set availability slots for an instructor."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: AvailabilityBulkSet) -> int:
        with self._uow:
            entries = [
                InstructorAvailability(
                    id=generate_id(),
                    instructor_id=data.instructor_id,
                    period_id=data.period_id,
                    day_of_week=slot.day_of_week,
                    period=slot.period,
                    is_available=slot.is_available,
                )
                for slot in data.slots
            ]
            count = self._uow.availabilities.bulk_save(entries)
            self._uow.commit()
            return count


class SetTeacherPreference:
    """Create or update an instructor preference."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: PreferenceCreate) -> InstructorPreference:
        with self._uow:
            entity = InstructorPreference(
                id=generate_id(),
                instructor_id=data.instructor_id,
                period_id=data.period_id,
                group_id=data.group_id,
                subject_id=data.subject_id,
                score=data.score,
            )
            saved = self._uow.preferences.save(entity)
            self._uow.commit()
            return saved
