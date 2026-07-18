"""Generated-schedule conflict validation (post-solve / post-edit).

Rules
-----
V-D21  No instructor may have two overlapping session blocks (same day,
       overlapping period range) within the same schedule run.
V-D22  No classroom may host two overlapping session blocks (same day,
       overlapping period range) within the same schedule run.

Unlike the other validators (which check catalog/offering data before the
solver runs), this one checks the *result* of a schedule run — it exists so
manual drag-and-drop edits to a published/generated schedule can be caught
before they violate the same hard constraints the solver itself enforces
(HD-05 no-overlap-teacher, HD-06 no-overlap-room).
"""

from __future__ import annotations

from collections import defaultdict

from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import ScheduleConflictValidationData

__all__ = ["ScheduleConflictValidator"]

_DAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class ScheduleConflictValidator(Validator[ScheduleConflictValidationData]):
    """Validates a generated schedule run for teacher/room double-booking."""

    def validate(self, data: ScheduleConflictValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        instructor_map = {i.id: i for i in data.instructors}
        classroom_map = {c.id: c for c in data.classrooms}
        subject_map = {s.id: s for s in data.subjects}
        group_map = {g.id: g for g in data.groups}
        assignment_map = {a.id: a for a in data.assignments}

        def block_label(block) -> str:
            assignment = assignment_map.get(block.assignment_id)
            group = group_map.get(assignment.group_id) if assignment else None
            subject = subject_map.get(group.subject_id) if group else None
            subject_name = subject.name if subject else "materia desconocida"
            group_number = group.group_number if group else "?"
            day_label = (
                _DAY_NAMES[block.day_of_week]
                if 0 <= block.day_of_week < len(_DAY_NAMES)
                else str(block.day_of_week)
            )
            return f"{subject_name} (grupo {group_number}) el {day_label} periodo {block.start_period}"

        self._check_instructor_conflicts(data, assignment_map, instructor_map, block_label, result)
        self._check_classroom_conflicts(data, classroom_map, block_label, result)

        return result

    # ── V-D21 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_instructor_conflicts(
        data: ScheduleConflictValidationData,
        assignment_map: dict,
        instructor_map: dict,
        block_label,
        result: ValidationResult,
    ) -> None:
        by_instructor_day: dict[tuple, list] = defaultdict(list)
        for block in data.session_blocks:
            assignment = assignment_map.get(block.assignment_id)
            if assignment is None:
                continue
            by_instructor_day[(assignment.instructor_id, block.day_of_week)].append(block)

        for (instructor_id, _day), blocks in by_instructor_day.items():
            for i in range(len(blocks)):
                for j in range(i + 1, len(blocks)):
                    a, b = blocks[i], blocks[j]
                    if ScheduleConflictValidator._periods_overlap(a, b):
                        instructor = instructor_map.get(instructor_id)
                        name = (
                            f"{instructor.first_name} {instructor.last_name}".strip()
                            if instructor else str(instructor_id)
                        )
                        result.add_error(
                            f"V-D21: El docente {name} tiene dos clases al mismo "
                            f"tiempo: {block_label(a)} choca con {block_label(b)}.",
                            entity_type="instructor", entity_id=instructor_id, entity_label=name,
                        )

    # ── V-D22 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_classroom_conflicts(
        data: ScheduleConflictValidationData,
        classroom_map: dict,
        block_label,
        result: ValidationResult,
    ) -> None:
        by_classroom_day: dict[tuple, list] = defaultdict(list)
        for block in data.session_blocks:
            by_classroom_day[(block.classroom_id, block.day_of_week)].append(block)

        for (classroom_id, _day), blocks in by_classroom_day.items():
            for i in range(len(blocks)):
                for j in range(i + 1, len(blocks)):
                    a, b = blocks[i], blocks[j]
                    if ScheduleConflictValidator._periods_overlap(a, b):
                        classroom = classroom_map.get(classroom_id)
                        label = (
                            f"{classroom.name} ({classroom.code})" if classroom else str(classroom_id)
                        )
                        result.add_error(
                            f"V-D22: El salón {label} tiene dos clases al mismo "
                            f"tiempo: {block_label(a)} choca con {block_label(b)}.",
                            entity_type="classroom", entity_id=classroom_id, entity_label=label,
                        )

    @staticmethod
    def _periods_overlap(a, b) -> bool:
        a_start, a_end = a.start_period, a.start_period + max(a.duration, 1)
        b_start, b_end = b.start_period, b.start_period + max(b.duration, 1)
        return a_start < b_end and b_start < a_end
