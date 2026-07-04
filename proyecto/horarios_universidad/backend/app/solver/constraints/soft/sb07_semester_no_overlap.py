"""SB-07: No solapamiento por semestre — Doc 06, Section SB-07."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

_logger = logging.getLogger(__name__)


class Sb07SemesterNoOverlap(AbstractConstraint):
    """Softly enforces that groups from the same plan+semester do not share a time slot.

    If groups_by_semester is empty (no plan_id/semester attributes on SolverGroup),
    the constraint is skipped gracefully.
    """

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-07",
            description=(
                "∑_{g ∈ G_{e,s}} ∑_a Z_{g,w,h,a} ≤ 1 + ξ_{e,s,w,h} ∀(e,s,w,h). "
                "Registers 'penalty_sb07' → dict[(plan,sem,w,h), BoolVar]."
            ),
            constraint_type="soft",
            math_reference="SB-07",
            module_path="constraints.soft.sb07_semester_no_overlap",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Z") is None:
            errors.append("SB-07: variable group 'Z' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-07: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        Z: dict = context.get_variable_group("Z")
        index = context._metadata["index"]

        groups_by_semester: dict = index.groups_by_semester
        if not groups_by_semester:
            _logger.warning(
                "SB-07: no groups_by_semester data — constraint skipped. "
                "Add plan_id and semester attributes to SolverGroup to enable it."
            )
            context.add_variable_group("penalty_sb07", {})
            return 0

        A_g: dict = index.A_g
        days: list[int] = index.days
        periods: list[int] = index.periods

        xi: dict = {}
        count = 0

        for (plan_id, semester), group_ids in groups_by_semester.items():
            if len(group_ids) < 2:
                continue  # single group — no overlap possible
            key_prefix = f"xi_sb07_p{str(plan_id)[:8]}_s{semester}"

            for w in days:
                for h in periods:
                    z_terms = []
                    for g_id in group_ids:
                        for a_id in A_g.get(g_id, []):
                            z_key = (g_id, w, h, a_id)
                            if z_key in Z:
                                z_terms.append(Z[z_key])

                    if len(z_terms) < 2:
                        continue  # can't overlap with fewer than 2 groups active

                    xi_var = model.NewBoolVar(f"{key_prefix}_w{w}_h{h}")
                    model.Add(sum(z_terms) <= 1 + xi_var)
                    xi[(plan_id, semester, w, h)] = xi_var
                    count += 1

        context.add_variable_group("penalty_sb07", xi)
        return count
