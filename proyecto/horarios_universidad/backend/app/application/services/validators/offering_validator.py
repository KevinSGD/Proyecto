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

        subject_map = {s.id: s for s in data.subjects}
        schedule_type_ids = {st.id for st in data.schedule_types}

        self._check_subject_references(data, subject_map, result)
        self._check_num_groups(data, subject_map, result)
        self._check_enrollment(data, subject_map, result)
        self._check_schedule_types(data, schedule_type_ids, subject_map, result)

        return result

    @staticmethod
    def _subject_label(subject_map: dict, subject_id) -> str:
        subject = subject_map.get(subject_id)
        return f"{subject.name} ({subject.code})" if subject else str(subject_id)

    # ── V-D14 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_subject_references(
        data: OfferingValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.subject_id not in subject_map:
                result.add_error(
                    f"V-D14: Una línea de oferta hace referencia a una "
                    f"materia que ya no existe (código {line.subject_id})."
                )

    # ── V-D15 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_num_groups(
        data: OfferingValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.num_groups <= 0:
                label = OfferingDataValidator._subject_label(subject_map, line.subject_id)
                result.add_error(
                    f"V-D15: La línea de oferta de {label} tiene 0 grupos "
                    f"configurados.",
                    entity_type="subject", entity_id=line.subject_id, entity_label=label,
                )

    # ── V-D16 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_enrollment(
        data: OfferingValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            if line.expected_enrollment_per_group <= 0:
                label = OfferingDataValidator._subject_label(subject_map, line.subject_id)
                result.add_error(
                    f"V-D16: La línea de oferta de {label} tiene 0 de cupo "
                    f"esperado por grupo.",
                    entity_type="subject", entity_id=line.subject_id, entity_label=label,
                )

    # ── V-D17 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_schedule_types(
        data: OfferingValidationData,
        schedule_type_ids: set[EntityId],
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        for line in data.offering_lines:
            label = OfferingDataValidator._subject_label(subject_map, line.subject_id)
            if line.schedule_type_id is None:
                result.add_warning(
                    f"V-D17: La línea de oferta de {label} no tiene un tipo "
                    f"de horario asignado.",
                    entity_type="subject", entity_id=line.subject_id, entity_label=label,
                )
            elif line.schedule_type_id not in schedule_type_ids:
                result.add_error(
                    f"V-D17: La línea de oferta de {label} hace referencia "
                    f"a un tipo de horario que ya no existe.",
                    entity_type="subject", entity_id=line.subject_id, entity_label=label,
                )
