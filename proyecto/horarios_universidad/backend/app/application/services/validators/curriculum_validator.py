"""Curriculum / study plan completeness validation.

Rules
-----
V-D21  Study plan must have subjects assigned to semesters.
V-D22  Each semester must have a reasonable credit load.
V-D23  Duplicate subject assignments within a plan are not allowed.
"""

from __future__ import annotations

from collections import defaultdict

from app.core.utils.types import EntityId
from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import CurriculumValidationData

__all__ = ["CurriculumValidator"]

# Reasonable credit-load boundaries per semester.
_MIN_CREDITS_PER_SEMESTER = 10
_MAX_CREDITS_PER_SEMESTER = 40


class CurriculumValidator(Validator[CurriculumValidationData]):
    """Validates curriculum/study plan completeness."""

    def validate(self, data: CurriculumValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        subject_map = {s.id: s for s in data.subjects}

        self._check_plan_has_subjects(data, result)
        self._check_semester_credit_load(data, subject_map, result)
        self._check_duplicate_assignments(data, result)

        return result

    # ── V-D21 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_plan_has_subjects(
        data: CurriculumValidationData,
        result: ValidationResult,
    ) -> None:
        plans_with_subjects: set[EntityId] = set()
        plan_ids: set[EntityId] = set()

        for ps in data.plan_subjects:
            plan_ids.add(ps.study_plan_id)
            plans_with_subjects.add(ps.study_plan_id)

        if not plan_ids:
            result.add_warning(
                "V-D21: No study plan data provided for validation."
            )
            return

        for pid in plan_ids:
            if pid not in plans_with_subjects:
                result.add_error(
                    f"V-D21: Study plan {pid} has no subjects assigned "
                    f"to any semester."
                )

    # ── V-D22 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_semester_credit_load(
        data: CurriculumValidationData,
        subject_map: dict,
        result: ValidationResult,
    ) -> None:
        credits_by_plan_semester: dict[
            tuple[EntityId, int], int
        ] = defaultdict(int)

        for ps in data.plan_subjects:
            subject = subject_map.get(ps.subject_id)
            if subject:
                credits_by_plan_semester[
                    (ps.study_plan_id, ps.semester)
                ] += subject.credit_hours

        for (plan_id, semester), credits in credits_by_plan_semester.items():
            if credits < _MIN_CREDITS_PER_SEMESTER:
                result.add_warning(
                    f"V-D22: Study plan {plan_id}, semester {semester} has "
                    f"only {credits} credits (minimum recommended: "
                    f"{_MIN_CREDITS_PER_SEMESTER})."
                )
            elif credits > _MAX_CREDITS_PER_SEMESTER:
                result.add_warning(
                    f"V-D22: Study plan {plan_id}, semester {semester} has "
                    f"{credits} credits (maximum recommended: "
                    f"{_MAX_CREDITS_PER_SEMESTER})."
                )

    # ── V-D23 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_duplicate_assignments(
        data: CurriculumValidationData,
        result: ValidationResult,
    ) -> None:
        seen: set[tuple[EntityId, EntityId]] = set()

        for ps in data.plan_subjects:
            key = (ps.study_plan_id, ps.subject_id)
            if key in seen:
                result.add_error(
                    f"V-D23: Subject {ps.subject_id} is assigned more than "
                    f"once in study plan {ps.study_plan_id}."
                )
            seen.add(key)
