"""HD-09: Disponibilidad docente — Doc 06, Section HD-09."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd09TeacherAvailability(AbstractConstraint):
    """If a slot is unavailable for instructor d, d cannot teach any group at that slot."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-09",
            description=(
                "If (w,h) ∉ available_slots(d): X_{d,g} → ¬Z_{g,w,h,a} "
                "for all g ∈ G_d, a ∈ A_g."
            ),
            constraint_type="hard",
            math_reference="HD-09",
            module_path="constraints.hard.hd09_teacher_availability",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("X", "Z"):
            if context.get_variable_group(name) is None:
                errors.append(f"HD-09: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-09: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        X: dict = context.get_variable_group("X")
        Z: dict = context.get_variable_group("Z")
        index = context._metadata["index"]

        instructors_by_id: dict = index.instructors_by_id
        G_d: dict = index.G_d
        A_g: dict = index.A_g
        T_g: dict = index.T_g

        count = 0
        for d_id, instructor in instructors_by_id.items():
            available: set[tuple[int, int]] = instructor.available_slots
            group_ids = G_d.get(d_id, [])

            for g_id in group_ids:
                x_key = (d_id, g_id)
                if x_key not in X:
                    continue
                x_var = X[x_key]
                rooms = A_g.get(g_id, [])

                # Only iterate slots the group could actually use
                for (w, h) in T_g.get(g_id, set()):
                    if (w, h) in available:
                        continue  # slot is allowed — no restriction needed

                    for a_id in rooms:
                        z_key = (g_id, w, h, a_id)
                        if z_key not in Z:
                            continue
                        model.AddImplication(x_var, Z[z_key].Not())
                        count += 1

        return count
