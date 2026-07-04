"""F6: Utilización equilibrada de aulas — Doc 07 Section 3.6.

Minimises the spread between the most-used and least-used classrooms:
    f6 = -(u_max - u_min)
    u_a = Σ_{g,w,h} Z_{g,w,h,a}   (usage count of room a)

Because CP-SAT variables must be created at model-building time, this component
creates u_max and u_min IntVars and the linking constraints inside compute_terms,
which has access to context.model.  This is a pragmatic deviation from a pure
"terms only" design, necessary because objective components are not guaranteed to
run during the constraint-building phase.

Returns [(u_max, -1), (u_min, +1)] so that the maximisation objective rewards
a smaller utilisation spread.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ortools.sat.python import cp_model

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F6RoomUtilization"]


class F6RoomUtilization(AbstractObjective):
    """Objective: balance room usage across all classrooms."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F6",
            description=(
                "Utilización de aulas: -(u_max − u_min) where u_a = Σ Z_{g,w,h,a}. "
                "Creates u_max/u_min vars and linking constraints inside compute_terms."
            ),
            weight=10,
            math_reference="Doc 07 Section 3.6",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Z") is None:
            errors.append("F6: variable group 'Z' is not registered.")
        if context.model is None:
            errors.append("F6: no CP-SAT model found in context.")
        return errors

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Create u_a, u_max, u_min variables and return objective terms.

        If Z is absent or the model is not initialised, returns an empty list.
        """
        Z: dict | None = context.get_variable_group("Z")
        model: cp_model.CpModel | None = context.model

        if Z is None or model is None:
            return []

        index = context._metadata.get("index")
        if index is None:
            return []

        classrooms_by_id: dict = index.classrooms_by_id
        A_g: dict = index.A_g

        # Build reverse map: room_id → list of Z vars that cover it.
        room_z_vars: dict[Any, list] = {a_id: [] for a_id in classrooms_by_id}
        for (g_id, w, h, a_id), z_var in Z.items():
            if a_id in room_z_vars:
                room_z_vars[a_id].append(z_var)

        # Skip rooms that are never referenced by any group.
        active_rooms = {a_id: vs for a_id, vs in room_z_vars.items() if vs}
        if not active_rooms:
            return []

        # Compute upper bound for utilisation (total group-slots = |Z| at most).
        max_usage = max(len(vs) for vs in active_rooms.values())

        u_max_var = model.NewIntVar(0, max_usage, "u_room_max")
        u_min_var = model.NewIntVar(0, max_usage, "u_room_min")

        # Create a usage variable for each active room and link it.
        for a_id, z_vars in active_rooms.items():
            short = str(a_id)[:8]
            u_a = model.NewIntVar(0, len(z_vars), f"u_room_{short}")
            model.Add(u_a == sum(z_vars))
            model.Add(u_max_var >= u_a)
            model.Add(u_min_var <= u_a)

        return [(u_max_var, -1), (u_min_var, 1)]
