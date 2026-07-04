"""HD-03: Vinculación inicio-cobertura — Doc 06, Section HD-03."""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd03StartCoverageLink(AbstractConstraint):
    """Links Y (block starts) to Z (coverage): if a block starts, Z=1 for all covered slots."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-03",
            description=(
                "Z_{g,w,h',a} ≥ Y_{g,l,w,h,a} for all (w,h') covered by starting at (w,h); "
                "and Z ≤ sum of Y that cover the slot (upper bound)."
            ),
            constraint_type="hard",
            math_reference="HD-03",
            module_path="constraints.hard.hd03_start_coverage_link",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("Y", "Z"):
            if context.get_variable_group(name) is None:
                errors.append(f"HD-03: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-03: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Y: dict = context.get_variable_group("Y")
        Z: dict = context.get_variable_group("Z")
        index = context._metadata["index"]

        coverage: dict = index.coverage
        groups_by_id: dict = index.groups_by_id
        A_g: dict = index.A_g

        # Build reverse index: (g, w, h', a) -> list[Y_var] that cover that slot
        covering_Y: dict = defaultdict(list)

        count = 0
        # Lower bound: Y implies Z for every covered slot
        for (g_id, l_idx, w, h_start), covered_slots in coverage.items():
            rooms = A_g.get(g_id, [])
            for a_id in rooms:
                y_key = (g_id, l_idx, w, h_start, a_id)
                if y_key not in Y:
                    continue
                y_var = Y[y_key]
                for (cov_w, cov_h) in covered_slots:
                    z_key = (g_id, cov_w, cov_h, a_id)
                    if z_key not in Z:
                        continue
                    model.AddImplication(y_var, Z[z_key])
                    count += 1
                    covering_Y[(g_id, cov_w, cov_h, a_id)].append(y_var)

        # Upper bound: Z_{g,w,h,a} <= sum of Y vars that cover (g,w,h,a)
        for (g_id, w, h, a_id), y_vars in covering_Y.items():
            z_key = (g_id, w, h, a_id)
            if z_key not in Z:
                continue
            model.Add(Z[z_key] <= sum(y_vars))
            count += 1

        return count
