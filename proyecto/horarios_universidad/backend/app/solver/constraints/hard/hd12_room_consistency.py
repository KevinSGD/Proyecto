"""HD-12: Consistencia de aula por grupo — Doc 06, Section HD-12."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd12RoomConsistency(AbstractConstraint):
    """All sessions of a group must use the same room (one room assigned per group)."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-12",
            description=(
                "∑_{a ∈ A_g} R_{g,a} = 1 and Z_{g,w,h,a} ≤ R_{g,a} ∀g, a, (w,h) — "
                "each group is pinned to exactly one classroom."
            ),
            constraint_type="hard",
            math_reference="HD-12",
            module_path="constraints.hard.hd12_room_consistency",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("Z", "R_room"):
            if context.get_variable_group(name) is None:
                errors.append(f"HD-12: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-12: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Z: dict = context.get_variable_group("Z")
        R_room: dict = context.get_variable_group("R_room")
        index = context._metadata["index"]

        groups_by_id: dict = index.groups_by_id
        A_g: dict = index.A_g
        T_g: dict = index.T_g

        count = 0
        for g_id in groups_by_id:
            rooms = A_g.get(g_id, [])

            # Exactly one room per group
            r_vars = [R_room[(g_id, a_id)] for a_id in rooms if (g_id, a_id) in R_room]
            if r_vars:
                model.AddExactlyOne(r_vars)
                count += 1

            # Every Z must be dominated by R
            for a_id in rooms:
                r_key = (g_id, a_id)
                if r_key not in R_room:
                    continue
                r_var = R_room[r_key]
                for (w, h) in T_g.get(g_id, set()):
                    z_key = (g_id, w, h, a_id)
                    if z_key not in Z:
                        continue
                    model.Add(Z[z_key] <= r_var)
                    count += 1

        return count
