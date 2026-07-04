"""Solver validation pipeline with built-in sanity checks — Doc 09 Module 2."""

from __future__ import annotations

from app.core.logging.logger import get_logger
from app.domain.interfaces.validation import ValidationResult
from app.solver.context import OptimizationProblem
from app.solver.validator.base import AbstractSolverValidator

__all__ = ["SolverValidationPipeline"]

_logger = get_logger(__name__)


class SolverValidationPipeline:
    """Runs registered validators and built-in checks V-01 through V-08."""

    def __init__(self) -> None:
        self._validators: list[AbstractSolverValidator] = []

    def add_validator(self, validator: AbstractSolverValidator) -> None:
        """Append a validator to the pipeline."""
        self._validators.append(validator)

    def validate(self, problem: OptimizationProblem) -> ValidationResult:
        """Execute all validators plus built-in checks V-01 – V-08."""
        result = ValidationResult.ok()

        for validator in self._validators:
            sub = validator.validate(problem)
            result.merge(sub)
            if sub.errors:
                _logger.warning(
                    "Validator '%s' reported %d error(s)",
                    validator.name,
                    len(sub.errors),
                )

        self._check_v01_candidate_instructors(problem, result)
        self._check_v02_compatible_classrooms(problem, result)
        self._check_v03_block_durations(problem, result)
        self._check_v04_valid_start_slots(problem, result)
        self._check_v05_block_duration_sum(problem, result)
        self._check_v06_instructor_slot_supply(problem, result)
        self._check_v07_contractual_limits(problem, result)
        self._check_v08_total_demand_supply(problem, result)

        return result

    # ------------------------------------------------------------------
    # Built-in checks
    # ------------------------------------------------------------------

    def _check_v01_candidate_instructors(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-01: Every group has at least 1 candidate instructor."""
        for group in problem.groups:
            if not group.candidate_instructors:
                result.add_error(
                    f"V-01: Group {group.id} (#{group.group_number}) "
                    "has no candidate instructors"
                )

    def _check_v02_compatible_classrooms(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-02: Every non-virtual group has at least 1 compatible classroom."""
        for group in problem.groups:
            if group.modality != "virtual" and not group.compatible_classrooms:
                result.add_error(
                    f"V-02: Group {group.id} (#{group.group_number}) "
                    "is non-virtual but has no compatible classrooms"
                )

    def _check_v03_block_durations(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-03: No block duration exceeds periods_per_day."""
        if problem.time_config is None:
            return
        ppd = problem.time_config.periods_per_day
        for group in problem.groups:
            for dur in group.block_durations:
                if dur > ppd:
                    result.add_error(
                        f"V-03: Group {group.id} has block duration "
                        f"{dur} which exceeds periods_per_day ({ppd})"
                    )

    def _check_v04_valid_start_slots(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-04: Every block has at least 1 valid start slot."""
        if problem.time_config is None:
            return
        ppd = problem.time_config.periods_per_day
        days = problem.time_config.days
        for group in problem.groups:
            for l_idx, dur in enumerate(group.block_durations):
                has_valid = any(
                    h + dur - 1 <= ppd
                    for _w in days
                    for h in range(1, ppd + 1)
                )
                if not has_valid:
                    result.add_error(
                        f"V-04: Group {group.id} block {l_idx} "
                        f"(duration={dur}) has no valid start slot"
                    )

    def _check_v05_block_duration_sum(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-05: sum(block_durations) == num_blocks * avg, i.e. length matches count."""
        for group in problem.groups:
            if len(group.block_durations) != group.num_blocks:
                result.add_error(
                    f"V-05: Group {group.id} declares num_blocks={group.num_blocks} "
                    f"but block_durations has {len(group.block_durations)} entries"
                )

    def _check_v06_instructor_slot_supply(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-06: Each candidate instructor has enough available slots."""
        instructor_map = {i.id: i for i in problem.instructors}
        for group in problem.groups:
            total_demand = sum(group.block_durations)
            for did in group.candidate_instructors:
                instructor = instructor_map.get(did)
                if instructor is None:
                    continue
                if len(instructor.available_slots) < total_demand:
                    result.add_warning(
                        f"V-06: Instructor {did} has {len(instructor.available_slots)} "
                        f"available slots but group {group.id} needs {total_demand} periods"
                    )

    def _check_v07_contractual_limits(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-07: Contractual limits coherent (min <= max weekly, max_daily <= max_weekly)."""
        for inst in problem.instructors:
            if inst.min_weekly_periods > inst.max_weekly_periods:
                result.add_error(
                    f"V-07: Instructor {inst.id} min_weekly_periods "
                    f"({inst.min_weekly_periods}) > max_weekly_periods "
                    f"({inst.max_weekly_periods})"
                )
            if inst.max_daily_periods > inst.max_weekly_periods:
                result.add_warning(
                    f"V-07: Instructor {inst.id} max_daily_periods "
                    f"({inst.max_daily_periods}) > max_weekly_periods "
                    f"({inst.max_weekly_periods}) — this is unusual"
                )

    def _check_v08_total_demand_supply(
        self, problem: OptimizationProblem, result: ValidationResult
    ) -> None:
        """V-08: Total period demand does not exceed total instructor capacity."""
        total_demand = sum(sum(g.block_durations) for g in problem.groups)
        total_supply = sum(i.max_weekly_periods for i in problem.instructors)
        if total_demand > total_supply:
            result.add_warning(
                f"V-08: Total demand ({total_demand} periods) exceeds "
                f"total instructor capacity ({total_supply} periods) — "
                "problem may be infeasible"
            )
