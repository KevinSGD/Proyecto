"""HD-06: No solapamiento de aula — Doc 06, Section HD-06."""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd06NoOverlapRoom(AbstractConstraint):
    """A non-virtual room can host at most one group in any given time slot."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-06",
            description=(
                "∑_{g: a ∈ A_g} Z_{g,w,h,a} ≤ 1 ∀a ∉ virtual, w, h — "
                "prevents double-booking of physical classrooms."
            ),
            constraint_type="hard",
            math_reference="HD-06",
            module_path="constraints.hard.hd06_no_overlap_room",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Z") is None:
            errors.append("HD-06: variable group 'Z' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-06: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Z: dict = context.get_variable_group("Z")
        index = context._metadata["index"]

        classrooms_by_id: dict = index.classrooms_by_id
        days: list = index.days
        periods: list = index.periods

        # Build reverse index: room_id -> [group_id] that may use it
        rooms_to_groups: dict = defaultdict(list)
        for g_id, rooms in index.A_g.items():
            for a_id in rooms:
                rooms_to_groups[a_id].append(g_id)

        count = 0
        for a_id, group_ids in rooms_to_groups.items():
            classroom = classrooms_by_id.get(a_id)
            if classroom is not None and classroom.is_virtual:
                continue  # HD-17 handles virtual rooms
            if len(group_ids) < 2:
                continue  # at most one group can use it — no conflict possible

            for w in days:
                for h in periods:
                    terms = [
                        Z[(g_id, w, h, a_id)]
                        for g_id in group_ids
                        if (g_id, w, h, a_id) in Z
                    ]
                    if len(terms) > 1:
                        model.AddAtMostOne(terms)
                        count += 1

        return count
