"""SB-05: Compacidad del horario docente — Doc 06, Section SB-05."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb05ScheduleCompactness(AbstractConstraint):
    """Minimises idle gaps between teaching sessions within each working day."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-05",
            description=(
                "ψ_d = ∑_w gaps_{d,w} where gaps_{d,w} = span_{d,w} − active_count_{d,w}. "
                "Links first_slot, last_slot, span, gaps via φ and δ. "
                "Registers 'penalty_sb05' → dict[instructor_id, IntVar]."
            ),
            constraint_type="soft",
            math_reference="SB-05",
            module_path="constraints.soft.sb05_schedule_compactness",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("phi", "delta", "first_slot", "last_slot", "span", "gaps"):
            if context.get_variable_group(name) is None:
                errors.append(f"SB-05: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-05: 'index' not found in context metadata.")
        return errors

    def _link_day_variables(
        self,
        model: cp_model.CpModel,
        d_id: object,
        w: int,
        periods: list[int],
        phi: dict,
        delta: dict,
        first_slot: dict,
        last_slot: dict,
        span: dict,
        gaps: dict,
    ) -> int:
        """Add linking constraints for (d, w)."""
        count = 0
        delta_dw = delta.get((d_id, w))
        first_dw = first_slot.get((d_id, w))
        last_dw = last_slot.get((d_id, w))
        span_dw = span.get((d_id, w))
        gaps_dw = gaps.get((d_id, w))

        if any(v is None for v in (delta_dw, first_dw, last_dw, span_dw, gaps_dw)):
            return 0

        active_phi = [phi[(d_id, w, h)] for h in periods if (d_id, w, h) in phi]
        if not active_phi:
            return 0

        # Bound first/last only when active slot exists
        for h in periods:
            phi_dw_h = phi.get((d_id, w, h))
            if phi_dw_h is None:
                continue
            model.Add(first_dw <= h).OnlyEnforceIf(phi_dw_h)
            model.Add(last_dw >= h).OnlyEnforceIf(phi_dw_h)
            count += 2

        # span when active; 0 when idle
        model.Add(span_dw == last_dw - first_dw + 1).OnlyEnforceIf(delta_dw)
        model.Add(span_dw == 0).OnlyEnforceIf(delta_dw.Not())
        count += 2

        # gaps = span - active count (only when active)
        active_sum = sum(active_phi)
        model.Add(gaps_dw == span_dw - active_sum).OnlyEnforceIf(delta_dw)
        model.Add(gaps_dw == 0).OnlyEnforceIf(delta_dw.Not())
        count += 2

        return count

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        phi: dict = context.get_variable_group("phi")
        delta: dict = context.get_variable_group("delta")
        first_slot: dict = context.get_variable_group("first_slot")
        last_slot: dict = context.get_variable_group("last_slot")
        span: dict = context.get_variable_group("span")
        gaps: dict = context.get_variable_group("gaps")
        index = context._metadata["index"]

        days: list[int] = index.days
        periods: list[int] = index.periods
        instructors_by_id = index.instructors_by_id

        count = 0
        penalty_sb05: dict = {}

        ppd = len(periods)
        for d_id in instructors_by_id:
            day_gap_vars = []
            for w in days:
                count += self._link_day_variables(
                    model, d_id, w, periods,
                    phi, delta, first_slot, last_slot, span, gaps,
                )
                gaps_dw = gaps.get((d_id, w))
                if gaps_dw is not None:
                    day_gap_vars.append(gaps_dw)

            if day_gap_vars:
                total_gaps = model.NewIntVar(
                    0, ppd * len(days), f"total_gaps_sb05_d{str(d_id)[:8]}"
                )
                model.Add(total_gaps == sum(day_gap_vars))
                penalty_sb05[d_id] = total_gaps
                count += 1

        context.add_variable_group("penalty_sb05", penalty_sb05)
        return count
