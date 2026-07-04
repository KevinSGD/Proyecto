"""HD-02: Ubicación exacta de bloque (inicio único) — Doc 06, Section HD-02."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd02BlockLocation(AbstractConstraint):
    """Each block of each group is placed in exactly one start slot and room."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-02",
            description=(
                "Each block l of group g has exactly one start: "
                "∑_{(w,h) ∈ T^ini_{g,l}} ∑_{a ∈ A_g} Y_{g,l,w,h,a} = 1 ∀g, l."
            ),
            constraint_type="hard",
            math_reference="HD-02",
            module_path="constraints.hard.hd02_block_location",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Y") is None:
            errors.append("HD-02: variable group 'Y' is not registered.")
        index = context._metadata.get("index")
        if index is None:
            errors.append("HD-02: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Y: dict = context.get_variable_group("Y")
        index = context._metadata["index"]

        groups_by_id: dict = index.groups_by_id
        T_g_l_ini: dict = index.T_g_l_ini
        A_g: dict = index.A_g

        count = 0
        for g_id, group in groups_by_id.items():
            for l_idx in range(group.num_blocks):
                starts = T_g_l_ini.get((g_id, l_idx), [])
                rooms = A_g.get(g_id, [])
                vars_for_block = [
                    Y[(g_id, l_idx, w, h, a_id)]
                    for (w, h) in starts
                    for a_id in rooms
                    if (g_id, l_idx, w, h, a_id) in Y
                ]
                if not vars_for_block:
                    continue
                model.AddExactlyOne(vars_for_block)
                count += 1

        return count
