"""SB-02: Balance de carga docente — Doc 06, Section SB-02."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb02WorkloadBalance(AbstractConstraint):
    """Minimises the spread between the busiest and least busy instructor."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-02",
            description=(
                "Minimise ω_max − ω_min across all instructors. "
                "Links omega_max/omega_min to omega; registers 'penalty_sb02' → (omega_max, omega_min)."
            ),
            constraint_type="soft",
            math_reference="SB-02",
            module_path="constraints.soft.sb02_workload_balance",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("omega") is None:
            errors.append("SB-02: variable group 'omega' is not registered.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        omega: dict = context.get_variable_group("omega")

        if not omega:
            context.add_variable_group("penalty_sb02", None)
            return 0

        # Retrieve or create global omega_max / omega_min variables.
        omega_max = context.get_variable_group("omega_max")
        omega_min = context.get_variable_group("omega_min")
        problem = context.problem
        max_wkly = max(
            (i.max_weekly_periods for i in problem.instructors), default=0
        )

        if omega_max is None:
            omega_max = model.NewIntVar(0, max_wkly, "omega_max")
            context.add_variable_group("omega_max", omega_max)

        if omega_min is None:
            omega_min = model.NewIntVar(0, max_wkly, "omega_min")
            context.add_variable_group("omega_min", omega_min)

        count = 0
        for d_id, omega_var in omega.items():
            model.Add(omega_max >= omega_var)
            model.Add(omega_min <= omega_var)
            count += 2

        context.add_variable_group("penalty_sb02", (omega_max, omega_min))
        return count
