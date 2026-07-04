"""F4: Compacidad del horario docente — Doc 07 Section 3.4.

Minimises idle gaps in each instructor's daily teaching schedule:
    f4 = -Σ_d Σ_w gaps_{d,w}

Each penalty_sb05 (per-instructor total-gap IntVar) or gaps[(d,w)] IntVar
contributes a term of coefficient -1 so that maximising the objective drives
gap counts toward zero.

Precedence:
1. penalty_sb05 dict[instructor_id, IntVar] — if SB-05 already computed totals.
2. gaps dict[(instructor_id, day), IntVar] — raw per-day gap counts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F4ScheduleCompactness"]


class F4ScheduleCompactness(AbstractObjective):
    """Objective: penalise idle gaps in instructors' daily schedules."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F4",
            description=(
                "Compacidad del horario: -Σ_d Σ_w gaps_{d,w}. "
                "Uses penalty_sb05 totals when available, else raw gaps."
            ),
            weight=20,
            math_reference="Doc 07 Section 3.4",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        has_penalty = context.get_variable_group("penalty_sb05") is not None
        has_gaps = context.get_variable_group("gaps") is not None
        if not has_penalty and not has_gaps:
            return [
                "F4: neither 'penalty_sb05' nor 'gaps' variable group is registered."
            ]
        return []

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Return negative-coefficient terms for each gap variable."""
        # Prefer aggregated totals from SB-05.
        penalty_sb05: dict | None = context.get_variable_group("penalty_sb05")
        if penalty_sb05 is not None:
            return [(var, -1) for var in penalty_sb05.values()]

        # Fallback: use raw per-day gap variables.
        gaps: dict | None = context.get_variable_group("gaps")
        if gaps is None:
            return []

        return [(var, -1) for var in gaps.values()]
