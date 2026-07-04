"""HD-10: Disponibilidad de aula — Doc 06, Section HD-10."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd10RoomAvailability(AbstractConstraint):
    """Z_{g,w,h,a} = 0 whenever slot (w,h) is outside room a's available_slots."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-10",
            description=(
                "For each room a and (w,h) ∉ available_slots(a): "
                "Z_{g,w,h,a} = 0 ∀g with a ∈ A_g."
            ),
            constraint_type="hard",
            math_reference="HD-10",
            module_path="constraints.hard.hd10_room_availability",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Z") is None:
            errors.append("HD-10: variable group 'Z' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-10: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Z: dict = context.get_variable_group("Z")
        index = context._metadata["index"]

        classrooms_by_id: dict = index.classrooms_by_id
        A_g: dict = index.A_g
        T_g: dict = index.T_g

        # Build room -> groups reverse index once
        room_to_groups: dict[object, list] = {}
        for g_id, rooms in A_g.items():
            for a_id in rooms:
                room_to_groups.setdefault(a_id, []).append(g_id)

        count = 0
        for a_id, group_ids in room_to_groups.items():
            classroom = classrooms_by_id.get(a_id)
            if classroom is None:
                continue
            available: set[tuple[int, int]] = classroom.available_slots

            for g_id in group_ids:
                for (w, h) in T_g.get(g_id, set()):
                    if (w, h) in available:
                        continue  # slot is allowed
                    z_key = (g_id, w, h, a_id)
                    if z_key not in Z:
                        continue
                    model.Add(Z[z_key] == 0)
                    count += 1

        return count
