"""F3: Satisfacción de preferencias horarias — Doc 07 Section 3.3.

Rewards placing instructors in their preferred (day, period) slots:
    f3 = Σ_d Σ_{w,h} pref^T_{d,w,h} · φ_{d,w,h}

Preference data is sourced from SB-04 reward terms (reward_sb04) when available.
As a fallback the component reads SolverInstructor.available_slots and assigns a
binary preference score (1 = available slot, slot not included = skipped).

If neither SB-04 data nor phi variables exist, returns an empty term list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F3TimeslotPreference"]


class F3TimeslotPreference(AbstractObjective):
    """Objective: reward instructors scheduled in their preferred timeslots."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F3",
            description=(
                "Preferencias horarias: Σ pref^T_{d,w,h} · φ_{d,w,h}. "
                "Reuses reward_sb04 when available."
            ),
            weight=20,
            math_reference="Doc 07 Section 3.3",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        has_phi = context.get_variable_group("phi") is not None
        has_sb04 = context.get_variable_group("reward_sb04") is not None
        if not has_phi and not has_sb04:
            return [
                "F3: neither 'phi' variables nor 'reward_sb04' are registered; "
                "timeslot preference terms cannot be computed."
            ]
        return []

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Return (φ_{d,w,h}, pref_score) pairs for available timeslots.

        SB-04 reward terms are preferred; falls back to a binary scan of phi.
        """
        reward_sb04: list[tuple[Any, int]] | None = context.get_variable_group("reward_sb04")
        if reward_sb04 is not None:
            return list(reward_sb04)

        # Fallback: derive from phi and available_slots.
        phi: dict | None = context.get_variable_group("phi")
        if phi is None:
            return []

        index = context._metadata.get("index")
        if index is None:
            return []

        instructors_by_id: dict = index.instructors_by_id
        terms: list[tuple[Any, int]] = []

        for (d_id, w, h), phi_var in phi.items():
            instructor = instructors_by_id.get(d_id)
            if instructor is None:
                continue
            if (w, h) in instructor.available_slots:
                terms.append((phi_var, 1))

        return terms
