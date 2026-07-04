"""SB-08: Distribución semanal equilibrada — Doc 06, Section SB-08."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb08WeeklyDistribution(AbstractConstraint):
    """Minimises each instructor's peak daily load to spread sessions evenly.

    For each instructor d we introduce ρ_d = max_w(ω_{d,w}).
    Minimising ∑_d ρ_d pushes loads away from single-day spikes.
    """

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-08",
            description=(
                "ρ_d = max_w ω_{d,w}; penalise ∑_d ρ_d. "
                "Registers 'penalty_sb08' → dict[instructor_id, IntVar]."
            ),
            constraint_type="soft",
            math_reference="SB-08",
            module_path="constraints.soft.sb08_weekly_distribution",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("omega_daily") is None:
            errors.append("SB-08: variable group 'omega_daily' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-08: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        omega_daily: dict = context.get_variable_group("omega_daily")
        index = context._metadata["index"]

        days: list[int] = index.days
        instructors_by_id = index.instructors_by_id

        count = 0
        penalty_sb08: dict = {}

        for d_id, instructor in instructors_by_id.items():
            daily_vars = [
                omega_daily[(d_id, w)]
                for w in days
                if (d_id, w) in omega_daily
            ]
            if not daily_vars:
                continue

            rho = model.NewIntVar(
                0, instructor.max_daily_periods,
                f"rho_sb08_d{str(d_id)[:8]}",
            )
            for daily_var in daily_vars:
                model.Add(rho >= daily_var)
                count += 1

            penalty_sb08[d_id] = rho

        context.add_variable_group("penalty_sb08", penalty_sb08)
        return count
