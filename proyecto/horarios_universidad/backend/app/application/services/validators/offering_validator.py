"""Academic offering consistency validation before optimization.

Rules
-----
V-D14  Every offering line must reference an existing subject.
V-D15  Every offering line must have num_groups > 0.
V-D16  Expected enrollment per group must be > 0.
V-D17  Schedule type must exist and be valid.
"""

from __future__ import annotations

from app.core.utils.types import EntityId
from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import OfferingValidationData

__all__ = ["OfferingDataValidator"]


class OfferingDataValidator(Validator[OfferingValidationData]):
    """Validates academic offering consistency."""

    def validate(self, data: OfferingValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        subject_ids = {s.id for s in data.subjects}
        schedule_type_ids = {st.id for st in data.schedule_types}

        self._check_subject_references(data, subject_ids, result)
        self._check_num_groups(data, result)
        self._check_enrollment(data, result)
        self._check_schedule_types(data, schedule_type_ids, result)

        return result

    # ── V-D14 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_subject_references(
        data: OfferingValidationData,
        subject_ids: set[EntityId],
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.subject_id not in subject_ids:
                result.add_error(
                    f"V-D14: Offering line {line.id} references "
                    f"non-existent subject {line.subject_id}."
                )

    # ── V-D15 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_num_groups(
        data: OfferingValidationData,
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.num_groups <= 0:
                result.add_error(
                    f"V-D15: Offering line {line.id} (subject "
                    f"{line.subject_id}) has num_groups={line.num_groups}."
                )

    # ── V-D16 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_enrollment(
        data: OfferingValidationData,
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.expected_enrollment_per_group <= 0:
                result.add_error(
                    f"V-D16: Offering line {line.id} (subject "
                    f"{line.subject_id}) has "
                    f"expected_enrollment_per_group="
                    f"{line.expected_enrollment_per_group}."
                )

    # ── V-D17 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_schedule_types(
        data: OfferingValidationData,
        schedule_type_ids: set[EntityId],
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.schedule_type_id is None:
                result.add_warning(
                    f"V-D17: Offering line {line.id} (subject "
                    f"{line.subject_id}) has no schedule type assigned."
                )
            elif line.schedule_type_id not in schedule_type_ids:
                result.add_error(
                    f"V-D17: Offering line {line.id} references "
                    f"non-existent schedule type {line.schedule_type_id}."
                )
