"""SB-04: Preferencia de franja horaria — Doc 06, Section SB-04."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Sb04TimeslotPreference(AbstractConstraint):
    """Rewards placing each instructor in their preferred (day, period) slots.

    Uses φ_{d,w,h} (active-in-slot indicator) as a proxy, since φ=1 means
    that instructor d is actually teaching at (w, h).  Preference data comes
    from SolverInstructor.available_slots which encodes hard availability;
    for a richer preference score the objective builder may scale these terms.

    Registers 'reward_sb04' → list[(phi_var, pref_score)].
    """

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-04",
            description=(
                "Reward ≈ α_franja * ∑_d ∑_{w,h} pref^T_{d,w,h} * φ_{d,w,h}. "
                "Registers 'reward_sb04' → list[(phi_var, coefficient)]."
            ),
            constraint_type="soft",
            math_reference="SB-04",
            module_path="constraints.soft.sb04_timeslot_preference",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("phi") is None:
            errors.append("SB-04: variable group 'phi' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-04: 'index' not found in context metadata.")
        return errors

    def apply(self, context: OptimizationContext) -> int:
        phi: dict = context.get_variable_group("phi")
        index = context._metadata["index"]
        instructors_by_id = index.instructors_by_id

        reward_terms: list[tuple] = []

        for (d_id, w, h), phi_var in phi.items():
            instructor = instructors_by_id.get(d_id)
            if instructor is None:
                continue
            # available_slots contains (day, period) pairs the instructor prefers.
            # We treat membership as a preference score of 1 (present/absent).
            # Richer integer scores can be layered in by the objective builder.
            if (w, h) in instructor.available_slots:
                reward_terms.append((phi_var, 1))

        context.add_variable_group("reward_sb04", reward_terms)
        return 0  # pure objective term — no constraints added
