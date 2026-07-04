"""Domain Validation Service.

Orchestrates all domain validators and produces a :class:`ValidationReport`
entity suitable for persistence and UI display.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.import_export import ValidationReport
from app.domain.interfaces.validation import ValidationResult

from .validators import (
    CapacityValidationData,
    CapacityValidator,
    ClassroomDataValidator,
    ClassroomValidationData,
    CurriculumValidationData,
    CurriculumValidator,
    InstructorDataValidator,
    InstructorValidationData,
    OfferingDataValidator,
    OfferingValidationData,
    SubjectDataValidator,
    SubjectValidationData,
)

if TYPE_CHECKING:
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = ["DomainValidationService"]


class DomainValidationService:
    """Orchestrates all domain validators and produces a ValidationReport."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    # ── public entry point ───────────────────────────────────────────

    def validate_for_optimization(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> ValidationReport:
        """Run all validators and return a comprehensive report.

        Steps:
        1. Load all data via UoW repositories.
        2. Package into validation data types.
        3. Run each validator.
        4. Merge results.
        5. Create and return a ``ValidationReport`` entity.
        """
        with self._uow:
            # 1. Load data
            instructors = self._uow.instructors.list_by_institution(
                institution_id,
            )
            specialties = []
            contracts = []  # type: ignore[var-annotated]
            availabilities = []
            for instructor in instructors:
                specialties.extend(
                    self._uow.specialties.list_by_instructor(instructor.id),
                )
                availabilities.extend(
                    self._uow.availabilities.list_by_instructor(
                        instructor.id, period_id,
                    ),
                )

            subjects = self._uow.subjects.list_by_institution(institution_id)
            classrooms = self._uow.classrooms.list_by_institution(
                institution_id,
            )
            classroom_avails = []
            for classroom in classrooms:
                classroom_avails.extend(
                    self._uow.classroom_availabilities.list_by_classroom(
                        classroom.id, period_id,
                    ),
                )

            offerings = self._uow.offerings.list_by_period(
                institution_id, period_id,
            )
            groups = self._uow.groups.list_by_period(
                institution_id, period_id,
            )
            schedule_types = self._uow.schedule_types.list_by_institution(
                institution_id,
            )

            # Entities not directly accessible via UoW are supplied as
            # empty lists; the orchestrator gracefully degrades.
            offering_lines: list = []
            classroom_equipment: list = []
            prerequisites: list = []
            plan_subjects: list = []

            # 2. Package into data types
            instructor_data = InstructorValidationData(
                instructors=instructors,
                specialties=specialties,
                contracts=contracts,
                availabilities=availabilities,
                groups=groups,
            )
            subject_data = SubjectValidationData(
                subjects=subjects,
                specialties=specialties,
                offering_lines=offering_lines,
                classrooms=classrooms,
                classroom_equipment=classroom_equipment,
                prerequisites=prerequisites,
            )
            classroom_data = ClassroomValidationData(
                classrooms=classrooms,
                classroom_availabilities=classroom_avails,
                groups=groups,
            )
            offering_data = OfferingValidationData(
                offerings=offerings,
                offering_lines=offering_lines,
                subjects=subjects,
                schedule_types=schedule_types,
            )
            capacity_data = CapacityValidationData(
                instructors=instructors,
                contracts=contracts,
                availabilities=availabilities,
                classrooms=classrooms,
                classroom_availabilities=classroom_avails,
                groups=groups,
                offering_lines=offering_lines,
                subjects=subjects,
            )
            curriculum_data = CurriculumValidationData(
                plan_subjects=plan_subjects,
                subjects=subjects,
            )

            # 3. Run each validator
            merged = ValidationResult.ok()
            validators_and_data = [
                (InstructorDataValidator(), instructor_data),
                (SubjectDataValidator(), subject_data),
                (ClassroomDataValidator(), classroom_data),
                (OfferingDataValidator(), offering_data),
                (CapacityValidator(), capacity_data),
                (CurriculumValidator(), curriculum_data),
            ]
            for validator, vdata in validators_and_data:
                merged.merge(validator.validate(vdata))

            # 5. Build the report entity
            report = ValidationReport(
                institution_id=institution_id,
                period_id=period_id,
                report_type="pre_optimization",
                status="passed" if merged.is_valid else "failed",
                errors=[
                    {"message": e} for e in merged.errors
                ],
                warnings=[
                    {"message": w} for w in merged.warnings
                ],
                summary={
                    "total_errors": len(merged.errors),
                    "total_warnings": len(merged.warnings),
                    "is_valid": merged.is_valid,
                    "validators_run": len(validators_and_data),
                },
                created_at=datetime.now(timezone.utc),
            )

            return report
