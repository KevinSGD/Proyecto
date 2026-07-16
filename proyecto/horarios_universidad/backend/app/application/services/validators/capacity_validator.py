"""Overall system capacity validation before optimization.

Rules
-----
V-D18  Total weekly hours demanded must not exceed total instructor capacity.
V-D19  Total groups must not exceed total classroom-slot capacity.
V-D20  No single day should be overloaded beyond available resources.
"""

from __future__ import annotations

from collections import defaultdict

from app.core.utils.types import EntityId
from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import CapacityValidationData

__all__ = ["CapacityValidator"]


class CapacityValidator(Validator[CapacityValidationData]):
    """Validates overall system capacity."""

    def validate(self, data: CapacityValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        self._check_instructor_capacity(data, result)
        self._check_classroom_capacity(data, result)
        self._check_daily_overload(data, result)

        return result

    # ── V-D18 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_instructor_capacity(
        data: CapacityValidationData,
        result: ValidationResult,
    ) -> None:
        subject_map = {s.id: s for s in data.subjects}

        total_demand_hours = 0
        for line in data.offering_lines:
            subject = subject_map.get(line.subject_id)
            if subject:
                total_demand_hours += line.num_groups * subject.weekly_hours

        total_supply_hours = 0
        active_instructor_ids = {i.id for i in data.instructors if i.is_active}
        for contract in data.contracts:
            if contract.is_active and contract.instructor_id in active_instructor_ids:
                total_supply_hours += contract.max_weekly_periods

        if total_supply_hours <= 0 and total_demand_hours > 0:
            result.add_error(
                "V-D18: No hay capacidad docente disponible, pero se "
                f"demandan {total_demand_hours} horas semanales."
            )
        elif total_demand_hours > total_supply_hours:
            result.add_error(
                f"V-D18: Las horas semanales demandadas ({total_demand_hours}) "
                f"superan la capacidad docente total disponible "
                f"({total_supply_hours})."
            )

    # ── V-D19 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_classroom_capacity(
        data: CapacityValidationData,
        result: ValidationResult,
    ) -> None:
        total_slots = 0
        for avail in data.classroom_availabilities:
            if avail.is_available:
                total_slots += 1

        subject_map = {s.id: s for s in data.subjects}

        total_group_slots_needed = 0
        for line in data.offering_lines:
            subject = subject_map.get(line.subject_id)
            if subject:
                total_group_slots_needed += line.num_groups * subject.weekly_hours

        if total_slots <= 0 and total_group_slots_needed > 0:
            result.add_error(
                "V-D19: No hay bloques de salón disponibles, pero se "
                f"necesitan {total_group_slots_needed} bloques de grupo."
            )
        elif total_group_slots_needed > total_slots:
            result.add_warning(
                f"V-D19: La demanda de bloques de grupo ({total_group_slots_needed}) "
                f"supera la oferta total de bloques de salón ({total_slots}). "
                f"El solver podría tener dificultades para encontrar una "
                f"solución factible."
            )

    # ── V-D20 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_daily_overload(
        data: CapacityValidationData,
        result: ValidationResult,
    ) -> None:
        instructor_avail_by_day: dict[int, int] = defaultdict(int)
        for avail in data.availabilities:
            if avail.is_available:
                instructor_avail_by_day[avail.day_of_week] += 1

        classroom_avail_by_day: dict[int, int] = defaultdict(int)
        for avail in data.classroom_availabilities:
            if avail.is_available:
                classroom_avail_by_day[avail.day_of_week] += 1

        if not instructor_avail_by_day and not classroom_avail_by_day:
            return

        total_groups = len(data.groups)
        if total_groups == 0:
            return

        days_with_avail = set(instructor_avail_by_day.keys()) | set(
            classroom_avail_by_day.keys()
        )
        num_active_days = len(days_with_avail) if days_with_avail else 1

        avg_groups_per_day = total_groups / num_active_days

        for day in sorted(days_with_avail):
            instructor_slots = instructor_avail_by_day.get(day, 0)
            classroom_slots = classroom_avail_by_day.get(day, 0)
            min_slots = min(instructor_slots, classroom_slots)

            if min_slots > 0 and avg_groups_per_day > min_slots:
                day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                day_label = day_names[day] if 0 <= day < len(day_names) else str(day)
                result.add_warning(
                    f"V-D20: El día {day_label} podría estar sobrecargado. "
                    f"Los bloques disponibles ({min_slots}) podrían ser "
                    f"insuficientes para la demanda diaria promedio "
                    f"(~{avg_groups_per_day:.0f} grupos)."
                )
