"""SB-10: Preferencia de aula — Doc 06, Section SB-10."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

_MAX_PREF = 5
_CAPACITY_BUCKET = 10  # wasted seats per bucket reduces score by 1


class Sb10RoomPreference(AbstractConstraint):
    """Rewards assigning groups to rooms that fit them best (minimal wasted capacity).

    When no explicit room-preference data exists on the group, a synthetic score
    is derived from how close the room capacity is to the expected enrolment:

        pref = clamp(MAX_PREF - excess_seats // CAPACITY_BUCKET, 1, MAX_PREF)

    Registers 'reward_sb10' → list[(R_room_var, preference_score)].
    """

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="SB-10",
            description=(
                "Reward = α_aula * ∑_g ∑_{a ∈ A_g} pref^A_{g,a} * R_{g,a}. "
                "Falls back to capacity-fit score if no explicit preference exists. "
                "Registers 'reward_sb10' → list[(R_room_var, score)]."
            ),
            constraint_type="soft",
            math_reference="SB-10",
            module_path="constraints.soft.sb10_room_preference",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("R_room") is None:
            errors.append("SB-10: variable group 'R_room' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("SB-10: 'index' not found in context metadata.")
        return errors

    @staticmethod
    def _capacity_score(enrollment: int, capacity: int) -> int:
        """Higher score = tighter fit (less wasted capacity)."""
        excess = max(0, capacity - enrollment)
        score = _MAX_PREF - excess // _CAPACITY_BUCKET
        return max(1, min(_MAX_PREF, score))

    def apply(self, context: OptimizationContext) -> int:
        R_room: dict = context.get_variable_group("R_room")
        index = context._metadata["index"]
        groups_by_id = index.groups_by_id
        classrooms_by_id = index.classrooms_by_id
        A_g: dict = index.A_g

        reward_terms: list[tuple] = []

        for g_id, group in groups_by_id.items():
            for a_id in A_g.get(g_id, []):
                r_key = (g_id, a_id)
                if r_key not in R_room:
                    continue
                classroom = classrooms_by_id.get(a_id)
                if classroom is None:
                    continue

                score = self._capacity_score(group.expected_enrollment, classroom.capacity)
                reward_terms.append((R_room[r_key], score))

        context.add_variable_group("reward_sb10", reward_terms)
        return 0  # pure objective term — no constraints added
