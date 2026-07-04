"""F1: Balance de carga docente — Doc 07 Section 3.1.

Minimises the weekly-load range across all instructors:
    f1 = -(ω_max - ω_min)

The maximisation objective receives terms [(ω_max, -1), (ω_min, +1)] so that a
smaller spread between the busiest and least-busy instructor is rewarded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F1WorkloadBalance"]


class F1WorkloadBalance(AbstractObjective):
    """Objective: minimise the spread between max and min weekly instructor load."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F1",
            description=(
                "Balance de carga docente: minimise ω_max − ω_min. "
                "Terms: [(ω_max, -1), (ω_min, +1)]."
            ),
            weight=50,
            math_reference="Doc 07 Section 3.1",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("omega_max") is None:
            errors.append("F1: variable 'omega_max' is not registered.")
        if context.get_variable_group("omega_min") is None:
            errors.append("F1: variable 'omega_min' is not registered.")
        return errors

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Return (ω_max, -1) and (ω_min, +1) to minimise the load range."""
        omega_max = context.get_variable_group("omega_max")
        omega_min = context.get_variable_group("omega_min")

        if omega_max is None or omega_min is None:
            return []

        return [(omega_max, -1), (omega_min, 1)]
