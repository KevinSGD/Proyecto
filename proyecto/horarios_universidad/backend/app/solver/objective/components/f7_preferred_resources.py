"""F7: Preferred resource bonus — rewards assigning groups to classrooms with preferred resources.

Groups whose subjects declare preferred (non-mandatory) resources receive a
positive objective bonus when assigned to a classroom that has any of those
resources.  No new solver variables are introduced — the bonus is expressed
directly over existing Z_{g,w,h,a} variables.

    f7 = +Σ_{g ∈ G_pref} Σ_{a ∈ pref(g)} Σ_{w,h} Z_{g,w,h,a}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["F7PreferredResources"]

_PREFERRED_WEIGHT = 200


class F7PreferredResources(AbstractObjective):
    """Objective: bonus for assigning groups to classrooms with preferred resources."""

    @property
    def info(self) -> ObjectiveInfo:
        return ObjectiveInfo(
            name="F7",
            description=(
                "Preferred resource bonus: +Σ Z_{g,w,h,a} for preferred classrooms. "
                "Uses existing Z variables — no new solver variables."
            ),
            weight=20,
            math_reference="Phase 10.5 — preferred resources",
            is_enabled=True,
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("Z") is None:
            errors.append("F7: variable group 'Z' is not registered.")
        return errors

    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        Z: dict | None = context.get_variable_group("Z")
        if Z is None:
            return []

        index = context._metadata.get("index")
        if index is None:
            return []

        terms: list[tuple[Any, int]] = []
        for group in context.problem.groups:
            if not group.preferred_classrooms:
                continue
            preferred_set = set(group.preferred_classrooms)
            for (g_id, w, h, a_id), z_var in Z.items():
                if g_id == group.id and a_id in preferred_set:
                    terms.append((z_var, _PREFERRED_WEIGHT))

        return terms
