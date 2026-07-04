"""HD-15: Carga máxima semanal — Doc 06, Section HD-15."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd15MaxWeeklyLoad(AbstractConstraint):
    """Instructor's total weekly teaching periods must not exceed max_weekly_periods."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-15",
            description=(
                "ω_d = ∑_{g ∈ G_d} hsem_g * X_{d,g} ≤ maxsem_d ∀d — "
                "weekly teaching load upper bound."
            ),
            constraint_type="hard",
            math_reference="HD-15",
            module_path="constraints.hard.hd15_max_weekly_load",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("X", "omega"):
            if context.get_variable_group(name) is None:
                errors.append(f"HD-15: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-15: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        X: dict = context.get_variable_group("X")
        omega: dict = context.get_variable_group("omega")
        index = context._metadata["index"]

        instructors_by_id: dict = index.instructors_by_id
        G_d: dict = index.G_d
        groups_by_id: dict = index.groups_by_id

        count = 0
        for d_id, omega_var in omega.items():
            instructor = instructors_by_id.get(d_id)
            if instructor is None:
                continue

            group_ids = G_d.get(d_id, [])
            terms: list = []
            for g_id in group_ids:
                x_key = (d_id, g_id)
                if x_key not in X:
                    continue
                group = groups_by_id.get(g_id)
                if group is None:
                    continue
                # hsem_g = total periods in all blocks
                hsem_g = sum(group.block_durations)
                terms.append(hsem_g * X[x_key])

            if terms:
                model.Add(omega_var == sum(terms))
                count += 1

            model.Add(omega_var <= instructor.max_weekly_periods)
            count += 1

        return count
