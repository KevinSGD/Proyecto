"""HD-05: No solapamiento de docente — Doc 06, Section HD-05."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd05NoOverlapTeacher(AbstractConstraint):
    """An instructor can teach at most one group in any given time slot."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-05",
            description=(
                "∑_{g ∈ G_d} ẑ_{d,g,w,h} ≤ 1 ∀d, w, h — "
                "uses Z_hat if available, otherwise falls back to φ."
            ),
            constraint_type="hard",
            math_reference="HD-05",
            module_path="constraints.hard.hd05_no_overlap_teacher",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context._metadata.get("index") is None:
            errors.append("HD-05: 'index' not found in context metadata.")
        return errors

    def _apply_via_z_hat(
        self,
        model: cp_model.CpModel,
        Z_hat: dict,
        index: object,
    ) -> int:
        """Enforce no-overlap using the pre-built ẑ variables."""
        G_d: dict = index.G_d
        days: list = index.days
        periods: list = index.periods

        count = 0
        for d_id, group_ids in G_d.items():
            for w in days:
                for h in periods:
                    terms = [
                        Z_hat[(d_id, g_id, w, h)]
                        for g_id in group_ids
                        if (d_id, g_id, w, h) in Z_hat
                    ]
                    if len(terms) > 1:
                        model.AddAtMostOne(terms)
                        count += 1
        return count

    def _apply_via_z(
        self,
        model: cp_model.CpModel,
        X: dict,
        Z: dict,
        index: object,
    ) -> int:
        """Fallback: for each (d, w, h) sum X*Z ≤ 1 via McCormick intermediates."""
        G_d: dict = index.G_d
        A_g: dict = index.A_g
        days: list = index.days
        periods: list = index.periods

        count = 0
        for d_id, group_ids in G_d.items():
            for w in days:
                for h in periods:
                    terms = []
                    for g_id in group_ids:
                        if (d_id, g_id) not in X:
                            continue
                        x_var = X[(d_id, g_id)]
                        for a_id in A_g.get(g_id, []):
                            z_key = (g_id, w, h, a_id)
                            if z_key not in Z:
                                continue
                            indicator = model.NewBoolVar(
                                f"novlap_d{d_id}_g{g_id}_w{w}_h{h}_a{a_id}"
                            )
                            model.Add(indicator <= x_var)
                            model.Add(indicator <= Z[z_key])
                            model.Add(indicator >= x_var + Z[z_key] - 1)
                            terms.append(indicator)
                            count += 3
                    if len(terms) > 1:
                        model.AddAtMostOne(terms)
                        count += 1
        return count

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        index = context._metadata["index"]
        Z_hat = context.get_variable_group("Z_hat")

        if Z_hat is not None:
            return self._apply_via_z_hat(model, Z_hat, index)

        X = context.get_variable_group("X")
        Z = context.get_variable_group("Z")
        if X is None or Z is None:
            return 0
        return self._apply_via_z(model, X, Z, index)
