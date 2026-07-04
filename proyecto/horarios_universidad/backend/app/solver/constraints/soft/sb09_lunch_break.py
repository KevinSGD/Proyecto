"""SB-09: Hora de almuerzo — Doc 06, Section SB-09."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

_DEFAULT_LUNCH_START = 5
_DEFAULT_LUNCH_END = 7


class Sb09LunchBreak(AbstractConstraint):
    """Ensures each active instructor has at least one free period during lunch.

    Parameters
    ----------
    lunch_start : int
        First period (1-indexed) of the lunch window (default 5).
    lunch_end : int
        Last period (1-indexed) of the lunch window (default 7).
    """

    def __init__(
        self,
        lunch_start: int = _DEFAULT_LUNCH_START,
        lunch_end: int = _DEFAULT_LUNCH_END,
    ) -> None:
        self._lunch_start = lunch_start
        self._lunch_end = lunch_end

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-09",
            description=(
                "∑_{h ∈ lunch} φ_{d,w,h} ≤ |lunch| − 1 + λ_{d,w} when δ_{d,w}=1. "
                "Registers 'penalty_sb09' → dict[(instructor_id, day), BoolVar]."
            ),
            constraint_type="soft",
            math_reference="SB-09",
            module_path="constraints.soft.sb09_lunch_break",
            parameters={
                "lunch_start": self._lunch_start,
                "lunch_end": self._lunch_end,
            },
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("phi", "delta"):
            if context.get_variable_group(name) is None:
                errors.append(f"SB-09: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-09: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        phi: dict = context.get_variable_group("phi")
        delta: dict = context.get_variable_group("delta")
        index = context._metadata["index"]

        days: list[int] = index.days
        instructors_by_id = index.instructors_by_id

        lunch_range = list(range(self._lunch_start, self._lunch_end + 1))
        if not lunch_range:
            context.add_variable_group("penalty_sb09", {})
            return 0

        count = 0
        penalty_sb09: dict = {}

        for d_id in instructors_by_id:
            for w in days:
                delta_dw = delta.get((d_id, w))
                if delta_dw is None:
                    continue

                lunch_phi = [
                    phi[(d_id, w, h)]
                    for h in lunch_range
                    if (d_id, w, h) in phi
                ]
                if not lunch_phi:
                    continue

                lambda_var = model.NewBoolVar(
                    f"lambda_sb09_d{str(d_id)[:8]}_w{w}"
                )
                # When active: allow at most (|lunch| - 1) busy lunch periods
                model.Add(
                    sum(lunch_phi) <= len(lunch_phi) - 1 + lambda_var
                ).OnlyEnforceIf(delta_dw)
                # When inactive: no violation
                model.Add(lambda_var == 0).OnlyEnforceIf(delta_dw.Not())

                penalty_sb09[(d_id, w)] = lambda_var
                count += 2

        context.add_variable_group("penalty_sb09", penalty_sb09)
        return count
