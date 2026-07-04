"""HD-16: Asignación fija — Doc 06, Section HD-16."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd16FixedAssignment(AbstractConstraint):
    """Force X_{d,g} = 1 when the group has a pre-fixed instructor assignment."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-16",
            description=(
                "X_{d,g} = 1 for groups whose SolverGroup carries a "
                "'fixed_instructor' attribute or has exactly one candidate. "
                "Ensures pre-determined assignments are honoured."
            ),
            constraint_type="hard",
            math_reference="HD-16",
            module_path="constraints.hard.hd16_fixed_assignment",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("X") is None:
            errors.append("HD-16: variable group 'X' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-16: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        X: dict = context.get_variable_group("X")
        index = context._metadata["index"]

        groups_by_id: dict = index.groups_by_id
        D_g: dict = index.D_g

        count = 0
        for g_id, group in groups_by_id.items():
            # Case 1: explicit fixed_instructor field on SolverGroup
            fixed_d_id = getattr(group, "fixed_instructor", None)
            if fixed_d_id is not None:
                x_key = (fixed_d_id, g_id)
                if x_key in X:
                    model.Add(X[x_key] == 1)
                    count += 1
                continue

            # Case 2: single candidate — assignment is implicitly fixed
            candidates = D_g.get(g_id, [])
            if len(candidates) == 1:
                x_key = (candidates[0], g_id)
                if x_key in X:
                    model.Add(X[x_key] == 1)
                    count += 1

        return count
