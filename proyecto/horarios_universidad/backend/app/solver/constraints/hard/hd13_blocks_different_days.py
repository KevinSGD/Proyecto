"""HD-13: Bloques en días distintos — Doc 06, Section HD-13."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd13BlocksDifferentDays(AbstractConstraint):
    """No two blocks of the same group may start on the same day."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-13",
            description=(
                "∑_l ∑_{h: (w,h) ∈ T^ini_{g,l}} ∑_a Y_{g,l,w,h,a} ≤ 1 ∀g (B_g ≥ 2), w — "
                "blocks of a group are spread across distinct days."
            ),
            constraint_type="hard",
            math_reference="HD-13",
            module_path="constraints.hard.hd13_blocks_different_days",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Y") is None:
            errors.append("HD-13: variable group 'Y' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-13: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Y: dict = context.get_variable_group("Y")
        index = context._metadata["index"]

        groups_by_id: dict = index.groups_by_id
        T_g_l_ini: dict = index.T_g_l_ini
        A_g: dict = index.A_g
        days: list = index.days

        count = 0
        for g_id, group in groups_by_id.items():
            if group.num_blocks < 2:
                continue  # single-block groups cannot have a day conflict
            rooms = A_g.get(g_id, [])

            for w in days:
                terms = [
                    Y[(g_id, l_idx, w, h, a_id)]
                    for l_idx in range(group.num_blocks)
                    for (start_w, h) in T_g_l_ini.get((g_id, l_idx), [])
                    if start_w == w
                    for a_id in rooms
                    if (g_id, l_idx, w, h, a_id) in Y
                ]
                if len(terms) > 1:
                    model.AddAtMostOne(terms)
                    count += 1

        return count
