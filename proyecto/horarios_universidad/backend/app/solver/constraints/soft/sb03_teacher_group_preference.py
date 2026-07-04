"""SB-03: Preferencia docente-grupo — Doc 06, Section SB-03."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb03TeacherGroupPreference(AbstractConstraint):
    """Rewards assigning instructors to groups they prefer.

    No CP-SAT constraints are added; reward data is registered for the
    objective builder as a list of (BoolVar, coefficient) pairs.
    """

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-03",
            description=(
                "Reward = α_pref * ∑_g ∑_{d ∈ D_g} pref_{d,g} * X_{d,g}. "
                "Registers 'reward_sb03' → list[(X_var, pref_value)]."
            ),
            constraint_type="soft",
            math_reference="SB-03",
            module_path="constraints.soft.sb03_teacher_group_preference",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("X") is None:
            errors.append("SB-03: variable group 'X' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-03: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        X: dict = context.get_variable_group("X")
        index = context._metadata["index"]
        instructors_by_id = index.instructors_by_id

        reward_terms: list[tuple] = []

        for (d_id, g_id), x_var in X.items():
            instructor = instructors_by_id.get(d_id)
            if instructor is None:
                continue
            # preferences is dict[group_id, score]
            pref_value = instructor.preferences.get(g_id, 0)
            if pref_value > 0:
                reward_terms.append((x_var, int(pref_value)))

        context.add_variable_group("reward_sb03", reward_terms)
        return 0  # pure objective term — no constraints added
