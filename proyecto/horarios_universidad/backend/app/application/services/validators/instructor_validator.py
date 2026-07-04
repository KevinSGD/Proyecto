"""Instructor data validation before optimization.

Rules
-----
V-D01  Every instructor must have at least one specialty.
V-D02  Every instructor must have a valid contract with workload limits > 0.
V-D03  Every instructor must have availability entries for the active period.
V-D04  No instructor should have max_daily > max_weekly.
V-D05  Instructors referenced by groups must exist and be active.
"""

from __future__ import annotations

from collections import defaultdict

from app.domain.interfaces.validation import ValidationResult, Validator

from .data_types import InstructorValidationData

__all__ = ["InstructorDataValidator"]


class InstructorDataValidator(Validator[InstructorValidationData]):
    """Validates instructor data before optimization."""

    def validate(self, data: InstructorValidationData) -> ValidationResult:
        result = ValidationResult.ok()

        instructor_map = {i.id: i for i in data.instructors}
        active_ids = {i.id for i in data.instructors if i.is_active}

        self._check_specialties(data, active_ids, result)
        self._check_contracts(data, active_ids, instructor_map, result)
        self._check_availability(data, active_ids, result)
        self._check_contract_consistency(data, instructor_map, result)
        self._check_group_references(data, instructor_map, active_ids, result)

        return result

    # ── V-D01 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_specialties(
        data: InstructorValidationData,
        active_ids: set,
        result: ValidationResult,
    ) -> None:
        specialties_by_instructor: dict[object, int] = defaultdict(int)
        for spec in data.specialties:
            specialties_by_instructor[spec.instructor_id] += 1

        for iid in active_ids:
            if specialties_by_instructor[iid] == 0:
                result.add_error(
                    f"V-D01: Instructor {iid} has no specialties assigned."
                )

    # ── V-D02 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_contracts(
        data: InstructorValidationData,
        active_ids: set,
        instructor_map: dict,
        result: ValidationResult,
    ) -> None:
        contracts_by_instructor: dict[object, list] = defaultdict(list)
        for contract in data.contracts:
            if contract.is_active:
                contracts_by_instructor[contract.instructor_id].append(contract)

        for iid in active_ids:
            active_contracts = contracts_by_instructor[iid]
            if not active_contracts:
                result.add_error(
                    f"V-D02: Instructor {iid} has no active contract."
                )
                continue

            for contract in active_contracts:
                if contract.max_weekly_periods <= 0:
                    result.add_error(
                        f"V-D02: Instructor {iid} contract {contract.id} "
                        f"has max_weekly_periods={contract.max_weekly_periods}."
                    )

    # ── V-D03 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_availability(
        data: InstructorValidationData,
        active_ids: set,
        result: ValidationResult,
    ) -> None:
        instructors_with_avail: set = set()
        for avail in data.availabilities:
            if avail.is_available:
                instructors_with_avail.add(avail.instructor_id)

        for iid in active_ids:
            if iid not in instructors_with_avail:
                result.add_error(
                    f"V-D03: Instructor {iid} has no availability entries "
                    f"for the active period."
                )

    # ── V-D04 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_contract_consistency(
        data: InstructorValidationData,
        instructor_map: dict,
        result: ValidationResult,
    ) -> None:
        for contract in data.contracts:
            if not contract.is_active:
                continue
            if (
                contract.max_daily_periods > 0
                and contract.max_weekly_periods > 0
                and contract.max_daily_periods > contract.max_weekly_periods
            ):
                result.add_error(
                    f"V-D04: Instructor {contract.instructor_id} contract "
                    f"{contract.id} has max_daily_periods "
                    f"({contract.max_daily_periods}) > max_weekly_periods "
                    f"({contract.max_weekly_periods})."
                )

    # ── V-D05 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_group_references(
        data: InstructorValidationData,
        instructor_map: dict,
        active_ids: set,
        result: ValidationResult,
    ) -> None:
        """Groups may carry an implicit instructor reference via specialties.

        Here we verify that every subject referenced by a group has at least
        one active instructor with a matching specialty.
        """
        subjects_with_active_instructors: set = set()
        for spec in data.specialties:
            if spec.instructor_id in active_ids:
                subjects_with_active_instructors.add(spec.subject_id)

        for group in data.groups:
            if group.subject_id not in subjects_with_active_instructors:
                result.add_warning(
                    f"V-D05: Group {group.id} (subject {group.subject_id}) "
                    f"has no active instructor with a matching specialty."
                )
