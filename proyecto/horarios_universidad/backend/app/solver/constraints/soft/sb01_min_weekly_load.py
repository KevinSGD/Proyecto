"""SB-01: Carga mínima semanal docente — Doc 06, Section SB-01."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb01MinWeeklyLoad(AbstractConstraint):
    """Penalises instructors whose weekly load falls below their declared minimum."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-01",
            description=(
                "σ⁻_d = max(0, minsem_d − ω_d) ∀d ∈ D. "
                "Registers 'penalty_sb01' → dict[instructor_id, IntVar]."
            ),
            constraint_type="soft",
            math_reference="SB-01",
            module_path="constraints.soft.sb01_min_weekly_load",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("omega") is None:
            errors.append("SB-01: variable group 'omega' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-01: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        omega: dict = context.get_variable_group("omega")
        index = context._metadata["index"]
        instructors_by_id = index.instructors_by_id

        sigma_minus: dict = {}
        count = 0

        for d_id, instructor in instructors_by_id.items():
            if d_id not in omega:
                continue
            min_periods = instructor.min_weekly_periods
            if min_periods <= 0:
                continue

            max_deficit = min_periods  # worst case: taught nothing
            var = model.NewIntVar(0, max_deficit, f"sigma_minus_sb01_d{str(d_id)[:8]}")
            model.Add(var >= min_periods - omega[d_id])
            sigma_minus[d_id] = var
            count += 1

        context.add_variable_group("penalty_sb01", sigma_minus)
        return count
