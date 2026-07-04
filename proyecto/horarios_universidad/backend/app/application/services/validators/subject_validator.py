"""Subject / course data validation before optimization.

Rules
-----
V-D06  Every subject must have credit_hours > 0.
V-D07  Every subject in an offering must have at least one qualified instructor.
V-D08  Every subject requiring equipment must have at least one compatible
       classroom.
V-D09  Subject prerequisites must not form cycles.
"""

from __future__ import annotations

from collections import defaultdict

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
        self._check_equipment_compatibility(data, subject_map, result)
        self._check_prerequisite_cycles(data, subject_map, result)

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
                    f"V-D06: Subject {subject.id} ({subject.code}) "
                    f"has credit_hours={subject.credit_hours}."
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
                code = subject.code if subject else "?"
                result.add_error(
                    f"V-D07: Offered subject {sid} ({code}) has no "
                    f"qualified instructor."
                )

    # ── V-D08 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_equipment_compatibility(
        data: SubjectValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        equipment_by_classroom: dict[EntityId, set[EntityId]] = defaultdict(set)
        for ce in data.classroom_equipment:
            equipment_by_classroom[ce.classroom_id].add(ce.equipment_id)

        active_classrooms = {c.id for c in data.classrooms if c.is_active}

        for subject in data.subjects:
            if not subject.is_active or not subject.required_equipment:
                continue

            required = set(subject.required_equipment)
            compatible_found = False

            for cid in active_classrooms:
                classroom_equip = equipment_by_classroom.get(cid, set())
                if required.issubset(classroom_equip):
                    compatible_found = True
                    break

            if not compatible_found:
                result.add_error(
                    f"V-D08: Subject {subject.id} ({subject.code}) requires "
                    f"equipment {required} but no compatible classroom exists."
                )

    # ── V-D09 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_prerequisite_cycles(
        data: SubjectValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        """Detect cycles in the prerequisite graph using DFS."""
        graph: dict[EntityId, list[EntityId]] = defaultdict(list)
        for prereq in data.prerequisites:
            graph[prereq.subject_id].append(prereq.prerequisite_subject_id)

        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[EntityId, int] = defaultdict(int)

        def dfs(node: EntityId) -> bool:
            color[node] = GRAY
            for neighbour in graph.get(node, []):
                if color[neighbour] == GRAY:
                    return True
                if color[neighbour] == WHITE and dfs(neighbour):
                    return True
            color[node] = BLACK
            return False

        for subject_id in graph:
            if color[subject_id] == WHITE:
                if dfs(subject_id):
                    subject = subject_map.get(subject_id)
                    code = subject.code if subject else "?"
                    result.add_error(
                        f"V-D09: Subject {subject_id} ({code}) is involved "
                        f"in a prerequisite cycle."
                    )
