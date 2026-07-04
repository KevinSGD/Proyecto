"""F2: Satisfacción de preferencias docente-grupo — Doc 07 Section 3.2.

Maximises total preference satisfaction across all instructor-group assignments:
    f2 = Σ_g Σ_{d ∈ D_g} pref_{d,g} · X_{d,g}

Preference scores come from SolverInstructor.preferences (dict[group_id → int]).
Only positive scores generate terms; zero/missing preferences are skipped.

If SB-03 has already registered reward_sb03 terms, those are reused directly to
avoid duplicating the preference signal in the objective.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F2TeacherGroupPreference"]


class F2TeacherGroupPreference(AbstractObjective):
    """Objective: reward instructor-group assignments that match declared preferences."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F2",
            description=(
                "Preferencias docente-grupo: Σ pref_{d,g} · X_{d,g}. "
                "Reuses reward_sb03 when available."
            ),
            weight=30,
            math_reference="Doc 07 Section 3.2",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("X") is None and context.get_variable_group("reward_sb03") is None:
            errors.append(
                "F2: neither variable group 'X' nor 'reward_sb03' is registered."
            )
        return errors

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Return (X_{d,g}, pref_score) pairs for all positive preferences.

        Preference list is read from SB-03 reward terms when present, falling
        back to a direct scan of X and instructor.preferences.
        """
        # Prefer pre-computed SB-03 terms to avoid double-counting.
        reward_sb03: list[tuple[Any, int]] | None = context.get_variable_group("reward_sb03")
        if reward_sb03 is not None:
            return list(reward_sb03)

        # Fallback: compute directly from X and instructor preferences.
        X: dict | None = context.get_variable_group("X")
        if X is None:
            return []

        index = context._metadata.get("index")
        if index is None:
            return []

        instructors_by_id: dict = index.instructors_by_id
        terms: list[tuple[Any, int]] = []

        for (d_id, g_id), x_var in X.items():
            instructor = instructors_by_id.get(d_id)
            if instructor is None:
                continue
            pref_score = instructor.preferences.get(g_id, 0)
            if pref_score > 0:
                terms.append((x_var, int(pref_score)))

        return terms
