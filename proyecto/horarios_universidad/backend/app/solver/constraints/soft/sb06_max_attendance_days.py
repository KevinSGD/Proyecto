"""SB-06: Días máximos de asistencia — Doc 06, Section SB-06."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb06MaxAttendanceDays(AbstractConstraint):
    """Penalises instructors who attend more days than their declared maximum."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-06",
            description=(
                "σ⁺_d = max(0, n_d − maxdias_d) ∀d with max_days set. "
                "Links n_days to δ; links δ to φ. "
                "Registers 'penalty_sb06' → dict[instructor_id, IntVar]."
            ),
            constraint_type="soft",
            math_reference="SB-06",
            module_path="constraints.soft.sb06_max_attendance_days",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("phi", "delta", "n_days"):
            if context.get_variable_group(name) is None:
                errors.append(f"SB-06: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-06: 'index' not found in context metadata.")
        return errors

    def _link_delta_to_phi(
        self,
        model: cp_model.CpModel,
        d_id: object,
        days: list[int],
        periods: list[int],
        phi: dict,
        delta: dict,
    ) -> int:
        """δ_{d,w} = 1 iff instructor d teaches at any period on day w."""
        count = 0
        for w in days:
            delta_dw = delta.get((d_id, w))
            if delta_dw is None:
                continue
            active = [phi[(d_id, w, h)] for h in periods if (d_id, w, h) in phi]
            if not active:
                continue
            # delta_dw >= phi for each h  (delta_dw=0 forces all phi=0)
            for phi_var in active:
                model.Add(delta_dw >= phi_var)
                count += 1
            # delta_dw <= sum of phi  (delta_dw=1 requires at least one phi=1)
            model.Add(delta_dw <= sum(active))
            count += 1
        return count

    def _link_n_days(
        self,
        model: cp_model.CpModel,
        d_id: object,
        days: list[int],
        delta: dict,
        n_days: dict,
    ) -> int:
        n_var = n_days.get(d_id)
        if n_var is None:
            return 0
        day_deltas = [delta[(d_id, w)] for w in days if (d_id, w) in delta]
        if not day_deltas:
            return 0
        model.Add(n_var == sum(day_deltas))
        return 1

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        phi: dict = context.get_variable_group("phi")
        delta: dict = context.get_variable_group("delta")
        n_days: dict = context.get_variable_group("n_days")
        index = context._metadata["index"]

        days: list[int] = index.days
        periods: list[int] = index.periods
        instructors_by_id = index.instructors_by_id

        count = 0
        penalty_sb06: dict = {}

        for d_id, instructor in instructors_by_id.items():
            count += self._link_delta_to_phi(model, d_id, days, periods, phi, delta)
            count += self._link_n_days(model, d_id, days, delta, n_days)

            max_days = instructor.max_days
            if max_days is None:
                continue

            n_var = n_days.get(d_id)
            if n_var is None:
                continue

            sigma_plus = model.NewIntVar(
                0, max(0, len(days) - max_days),
                f"sigma_plus_sb06_d{str(d_id)[:8]}",
            )
            model.Add(sigma_plus >= n_var - max_days)
            penalty_sb06[d_id] = sigma_plus
            count += 1

        context.add_variable_group("penalty_sb06", penalty_sb06)
        return count
