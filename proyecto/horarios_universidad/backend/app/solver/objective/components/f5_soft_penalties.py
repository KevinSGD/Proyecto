"""F5: Penalizaciones por restricciones blandas — Doc 07 Section 3.5.

Aggregates all soft-constraint penalty and reward variables into objective terms:
    f5 = -Σ_s p_s · v_s + Σ_r r_r · b_r

Sub-weights follow the SB priority table:
    SB-02: 2000   SB-01: 1500   SB-09: 1000   SB-05: 500
    SB-06: 400    SB-08: 200    SB-11: 150     SB-04: 100    SB-10: 50
    SB-03: 300 (reward — positive coefficient)

Each penalty variable receives a negative coefficient × sub-weight (so that
maximising the objective means minimising penalties).
Each reward variable (already handled by SB-03 / SB-04) receives a positive
coefficient so this component can still include them if not handled elsewhere.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F5SoftPenalties"]

# Sub-weights for each soft-constraint penalty (positive = penalty weight to negate).
_PENALTY_WEIGHTS: dict[str, int] = {
    "penalty_sb02": 2000,
    "penalty_sb01": 1500,
    "penalty_sb09": 1000,
    "penalty_sb05": 500,
    "penalty_sb06": 400,
    "penalty_sb08": 200,
    "penalty_sb11": 150,
    "penalty_sb04": 100,
    "penalty_sb10": 50,
}

# Reward term groups contribute positively.
_REWARD_WEIGHTS: dict[str, int] = {
    "reward_sb03": 300,
    "reward_sb04": 100,
    "reward_sb10": 50,
}


class F5SoftPenalties(AbstractObjective):
    """Objective: aggregate all soft-constraint penalties and rewards."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F5",
            description=(
                "Penalizaciones blandas: -Σ p_s·v_s + Σ r_r·b_r. "
                "Collects penalty_sb01..11 and reward_sb03/04/10."
            ),
            weight=80,
            math_reference="Doc 07 Section 3.5",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        # This component is opportunistic — it uses whatever penalty/reward
        # variables happen to be registered.  No hard requirements.
        return []

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Collect penalty (negative) and reward (positive) terms."""
        terms: list[tuple[Any, int]] = []

        # Penalty variables — negate so that maximisation minimises them.
        for group_name, sub_weight in _PENALTY_WEIGHTS.items():
            group = context.get_variable_group(group_name)
            if group is None:
                continue
            terms.extend(
                self._extract_penalty_terms(group_name, group, sub_weight)
            )

        # Reward variables — add positively.
        for group_name, sub_weight in _REWARD_WEIGHTS.items():
            group = context.get_variable_group(group_name)
            if group is None:
                continue
            terms.extend(
                self._extract_reward_terms(group_name, group, sub_weight)
            )

        return terms

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_penalty_terms(
        self, name: str, group: Any, sub_weight: int
    ) -> list[tuple[Any, int]]:
        """Extract (var, -sub_weight) pairs from a penalty group."""
        # SB-02 stores a tuple (omega_max, omega_min) — handled specially.
        if name == "penalty_sb02":
            if isinstance(group, tuple) and len(group) == 2:
                omega_max, omega_min = group
                if omega_max is not None and omega_min is not None:
                    return [(omega_max, -sub_weight), (omega_min, sub_weight)]
            return []

        # Most penalty groups are dict[key, IntVar].
        if isinstance(group, dict):
            return [(var, -sub_weight) for var in group.values() if var is not None]

        # List-of-(var, coeff) format.
        if isinstance(group, list):
            return [(var, -sub_weight * coeff) for var, coeff in group if var is not None]

        return []

    def _extract_reward_terms(
        self, name: str, group: Any, sub_weight: int
    ) -> list[tuple[Any, int]]:
        """Extract (var, +sub_weight * coeff) pairs from a reward group."""
        if isinstance(group, list):
            return [
                (var, sub_weight * coeff) for var, coeff in group if var is not None
            ]

        if isinstance(group, dict):
            return [(var, sub_weight) for var in group.values() if var is not None]

        return []
