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

        self._check_capacity(data, result)
        self._check_presential_groups(data, classroom_map, result)
        self._check_availability_coverage(data, result)
        self._check_duplicate_availability(data, result)

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
                result.add_error(
                    f"V-D10: Classroom {classroom.id} ({classroom.code}) "
                    f"has capacity={classroom.capacity}."
                )

    # ── V-D11 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_presential_groups(
        data: ClassroomValidationData,
        classroom_map: dict,
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
                result.add_error(
                    f"V-D11: Presential group {group.id} "
                    f"(enrollment={group.expected_enrollment}) has no "
                    f"compatible classroom with sufficient capacity."
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
                result.add_warning(
                    f"V-D12: Classroom {classroom.id} ({classroom.code}) "
                    f"has no availability entries for the active period."
                )

    # ── V-D13 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_duplicate_availability(
        data: ClassroomValidationData,
        result: ValidationResult,
    ) -> None:
        seen: set[Tuple[EntityId, int, int]] = set()

        for avail in data.classroom_availabilities:
            key = (avail.classroom_id, avail.day_of_week, avail.period)
            if key in seen:
                result.add_error(
                    f"V-D13: Duplicate availability entry for classroom "
                    f"{avail.classroom_id} on day {avail.day_of_week}, "
                    f"period {avail.period}."
                )
            seen.add(key)
