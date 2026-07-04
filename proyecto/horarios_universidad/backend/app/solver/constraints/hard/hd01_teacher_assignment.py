"""HD-01: Asignación única de docente — Doc 06, Section HD-01."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd01TeacherAssignment(AbstractConstraint):
    """Each group is assigned exactly one instructor."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-01",
            description="Each group gets exactly one instructor: ∑_{d ∈ D_g} X_{d,g} = 1 ∀g.",
            constraint_type="hard",
            math_reference="HD-01",
            module_path="constraints.hard.hd01_teacher_assignment",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("X") is None:
            errors.append("HD-01: variable group 'X' is not registered.")
        index = context._metadata.get("index")
        if index is None:
            errors.append("HD-01: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        X: dict = context.get_variable_group("X")
        index = context._metadata["index"]
        D_g: dict = index.D_g

        count = 0
        for g_id, candidate_ids in D_g.items():
            vars_for_group = [X[(d_id, g_id)] for d_id in candidate_ids if (d_id, g_id) in X]
            if not vars_for_group:
                continue
            model.AddExactlyOne(vars_for_group)
            count += 1

        return count
