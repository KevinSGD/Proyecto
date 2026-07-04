"""SB-11: Concentración matutino/vespertino — Doc 06, Section SB-11."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb11SessionConcentration(AbstractConstraint):
    """Penalises instructors who split sessions between morning and afternoon.

    For each (instructor, day) we compute:
        τ_{d,w} = min(μ^M_{d,w}, μ^V_{d,w})
    where μ^M (μ^V) is the count of active periods before (after) the
    midpoint of the day.  Minimising τ encourages concentration in one half.
    """

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-11",
            description=(
                "τ_{d,w} = min(μ^M_{d,w}, μ^V_{d,w}); penalise ∑_d ∑_w τ_{d,w}. "
                "Registers 'penalty_sb11' → dict[(instructor_id, day), IntVar]."
            ),
            constraint_type="soft",
            math_reference="SB-11",
            module_path="constraints.soft.sb11_session_concentration",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("phi") is None:
            errors.append("SB-11: variable group 'phi' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-11: 'index' not found in context metadata.")
        return errors

    def _add_tau_for_day(
        self,
        model: cp_model.CpModel,
        d_id: object,
        w: int,
        periods: list[int],
        phi: dict,
    ) -> cp_model.IntVar | None:
        """Create and return τ_{d,w} = min(morning_count, afternoon_count)."""
        h_mid = len(periods) // 2  # split index (0-based count of morning periods)
        # periods is 1-indexed [1, 2, ..., ppd]
        morning_periods = [h for h in periods if h <= h_mid]
        afternoon_periods = [h for h in periods if h > h_mid]

        mu_m = [phi[(d_id, w, h)] for h in morning_periods if (d_id, w, h) in phi]
        mu_v = [phi[(d_id, w, h)] for h in afternoon_periods if (d_id, w, h) in phi]

        if not mu_m or not mu_v:
            return None

        max_half = max(len(mu_m), len(mu_v))
        tau = model.NewIntVar(0, max_half, f"tau_sb11_d{str(d_id)[:8]}_w{w}")
        model.Add(tau <= sum(mu_m))
        model.Add(tau <= sum(mu_v))
        # The objective will push tau down to the actual minimum.
        return tau

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        phi: dict = context.get_variable_group("phi")
        index = context._metadata["index"]

        days: list[int] = index.days
        periods: list[int] = index.periods
        instructors_by_id = index.instructors_by_id

        count = 0
        penalty_sb11: dict = {}

        for d_id in instructors_by_id:
            for w in days:
                tau = self._add_tau_for_day(model, d_id, w, periods, phi)
                if tau is None:
                    continue
                penalty_sb11[(d_id, w)] = tau
                count += 2  # two bounding constraints per tau

        context.add_variable_group("penalty_sb11", penalty_sb11)
        return count
