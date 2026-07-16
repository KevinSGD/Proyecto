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

        self._check_specialties(data, active_ids, instructor_map, result)
        self._check_contracts(data, active_ids, instructor_map, result)
        self._check_availability(data, active_ids, instructor_map, result)
        self._check_contract_consistency(data, instructor_map, result)
        self._check_group_references(data, instructor_map, active_ids, result)

        return result

    @staticmethod
    def _name(instructor_map: dict, iid) -> str:
        instructor = instructor_map.get(iid)
        return f"{instructor.first_name} {instructor.last_name}".strip() if instructor else str(iid)

    # ── V-D01 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_specialties(
        data: InstructorValidationData,
        active_ids: set,
        instructor_map: dict,
        result: ValidationResult,
    ) -> None:
        specialties_by_instructor: dict[object, int] = defaultdict(int)
        for spec in data.specialties:
            specialties_by_instructor[spec.instructor_id] += 1

        for iid in active_ids:
            if specialties_by_instructor[iid] == 0:
                name = InstructorDataValidator._name(instructor_map, iid)
                result.add_error(
                    f"V-D01: El docente {name} no tiene ninguna materia "
                    f"(especialidad) asignada."
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
            name = InstructorDataValidator._name(instructor_map, iid)
            active_contracts = contracts_by_instructor[iid]
            if not active_contracts:
                result.add_error(
                    f"V-D02: El docente {name} no tiene un contrato activo."
                )
                continue

            for contract in active_contracts:
                if contract.max_weekly_periods <= 0:
                    result.add_error(
                        f"V-D02: El contrato del docente {name} tiene "
                        f"0 horas semanales máximas configuradas."
                    )

    # ── V-D03 ────────────────────────────────────────────────────────

    @staticmethod
    def _check_availability(
        data: InstructorValidationData,
        active_ids: set,
        instructor_map: dict,
        result: ValidationResult,
    ) -> None:
        instructors_with_avail: set = set()
        for avail in data.availabilities:
            if avail.is_available:
                instructors_with_avail.add(avail.instructor_id)

        for iid in active_ids:
            if iid not in instructors_with_avail:
                name = InstructorDataValidator._name(instructor_map, iid)
                result.add_error(
                    f"V-D03: El docente {name} no tiene horarios de "
                    f"disponibilidad registrados para el período activo."
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
                name = InstructorDataValidator._name(
                    instructor_map, contract.instructor_id,
                )
                result.add_error(
                    f"V-D04: El contrato del docente {name} tiene un máximo "
                    f"diario ({contract.max_daily_periods}h) mayor que el "
                    f"máximo semanal ({contract.max_weekly_periods}h)."
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

        subject_map = {s.id: s for s in data.subjects}

        for group in data.groups:
            if group.subject_id not in subjects_with_active_instructors:
                subject = subject_map.get(group.subject_id)
                subject_label = subject.name if subject else str(group.subject_id)
                result.add_warning(
                    f"V-D05: El grupo {group.group_number} de {subject_label} "
                    f"no tiene ningún docente activo con esa especialidad "
                    f"asignada."
                )
