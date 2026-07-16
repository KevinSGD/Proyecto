"""Subject / course data validation before optimization.

Rules
-----
V-D06  Every subject must have credit_hours > 0.
V-D07  Every subject in an offering must have at least one qualified instructor.
"""

from __future__ import annotations

from app.core.utils.types import EntityId
from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import SubjectValidationData

__all__ = ["SubjectDataValidator"]


class SubjectDataValidator(Validator[SubjectValidationData]):
    """Validates subject/course data."""

    def validate(self, data: SubjectValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        subject_map = {s.id: s for s in data.subjects}

        self._check_credit_hours(data, result)
        self._check_qualified_instructors(data, subject_map, result)

        return result

    # ── V-D06 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_credit_hours(
        data: SubjectValidationData,
        result: ValidationResult,
    ) -> None:
        for subject in data.subjects:
            if not subject.is_active:
                continue
            if subject.credit_hours <= 0:
                result.add_error(
                    f"V-D06: La materia {subject.name} ({subject.code}) "
                    f"tiene 0 créditos configurados."
                )

    # ── V-D07 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_qualified_instructors(
        data: SubjectValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        subjects_with_instructors: set[EntityId] = set()
        for spec in data.specialties:
            subjects_with_instructors.add(spec.subject_id)

        offered_subject_ids = {line.subject_id for line in data.offering_lines}

        for sid in offered_subject_ids:
            if sid not in subjects_with_instructors:
                subject = subject_map.get(sid)
                label = f"{subject.name} ({subject.code})" if subject else str(sid)
                result.add_error(
                    f"V-D07: La materia ofertada {label} no tiene ningún "
                    f"docente calificado (especialidad) asignado."
                )
