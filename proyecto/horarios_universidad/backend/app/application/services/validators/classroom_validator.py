"""Classroom / room data validation before optimization.

Rules
-----
V-D10  Every classroom must have capacity > 0.
V-D11  Presential groups must have at least one compatible classroom.
V-D12  Classroom availability must cover active period days.
V-D13  No duplicate availability entries (same classroom + day + period).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Tuple

from app.core.utils.types import EntityId
from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import ClassroomValidationData

__all__ = ["ClassroomDataValidator"]


class ClassroomDataValidator(Validator[ClassroomValidationData]):
    """Validates classroom/room data."""

    def validate(self, data: ClassroomValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        classroom_map = {c.id: c for c in data.classrooms}
        subject_map = {s.id: s for s in data.subjects}

        self._check_capacity(data, result)
        self._check_presential_groups(data, subject_map, result)
        self._check_availability_coverage(data, result)
        self._check_duplicate_availability(data, classroom_map, result)

        return result

    # ── V-D10 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_capacity(
        data: ClassroomValidationData,
        result: ValidationResult,
    ) -> None:
        for classroom in data.classrooms:
            if not classroom.is_active:
                continue
            if classroom.is_virtual:
                continue
            if classroom.capacity <= 0:
                label = f"{classroom.name} ({classroom.code})"
                result.add_error(
                    f"V-D10: El salón {label} tiene 0 de capacidad configurada.",
                    entity_type="classroom", entity_id=classroom.id, entity_label=label,
                )

    # ── V-D11 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_presential_groups(
        data: ClassroomValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        active_physical = [
            c for c in data.classrooms
            if c.is_active and not c.is_virtual and c.capacity > 0
        ]

        for group in data.groups:
            if group.modality != "presential":
                continue

            compatible = any(
                c.capacity >= group.expected_enrollment
                for c in active_physical
            )

            if not compatible:
                subject = subject_map.get(group.subject_id)
                subject_label = subject.name if subject else str(group.subject_id)
                result.add_error(
                    f"V-D11: El grupo {group.group_number} de {subject_label} "
                    f"(cupo={group.expected_enrollment}) no tiene ningún "
                    f"salón presencial con capacidad suficiente.",
                    entity_type="subject", entity_id=group.subject_id, entity_label=subject_label,
                )

    # ── V-D12 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_availability_coverage(
        data: ClassroomValidationData,
        result: ValidationResult,
    ) -> None:
        avail_days: dict[EntityId, set[int]] = defaultdict(set)
        for avail in data.classroom_availabilities:
            if avail.is_available:
                avail_days[avail.classroom_id].add(avail.day_of_week)

        for classroom in data.classrooms:
            if not classroom.is_active or classroom.is_virtual:
                continue
            if classroom.id not in avail_days:
                label = f"{classroom.name} ({classroom.code})"
                result.add_warning(
                    f"V-D12: El salón {label} no tiene horarios de "
                    f"disponibilidad registrados para el período activo.",
                    entity_type="classroom", entity_id=classroom.id, entity_label=label,
                )

    # ── V-D13 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_duplicate_availability(
        data: ClassroomValidationData,
        classroom_map: dict,
        result: ValidationResult,
    ) -> None:
        seen: set[Tuple[EntityId, int, int]] = set()
        day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        for avail in data.classroom_availabilities:
            key = (avail.classroom_id, avail.day_of_week, avail.period)
            if key in seen:
                classroom = classroom_map.get(avail.classroom_id)
                classroom_label = classroom.name if classroom else str(avail.classroom_id)
                day_label = day_names[avail.day_of_week] if 0 <= avail.day_of_week < len(day_names) else str(avail.day_of_week)
                result.add_error(
                    f"V-D13: El salón {classroom_label} tiene disponibilidad "
                    f"duplicada el día {day_label}, período {avail.period}.",
                    entity_type="classroom", entity_id=avail.classroom_id, entity_label=classroom_label,
                )
            seen.add(key)
