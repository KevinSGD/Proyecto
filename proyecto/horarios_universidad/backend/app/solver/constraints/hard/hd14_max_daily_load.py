"""HD-14: Carga máxima diaria — Doc 06, Section HD-14."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd14MaxDailyLoad(AbstractConstraint):
    """Instructor's total periods taught on any single day must not exceed max_daily_periods."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-14",
            description="ω_{d,w} ≤ maxdia_d ∀d, w — daily teaching load upper bound.",
            constraint_type="hard",
            math_reference="HD-14",
            module_path="constraints.hard.hd14_max_daily_load",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        if context.get_variable_group("omega_daily") is None:
            errors.append("HD-14: variable group 'omega_daily' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-14: 'index' not found in context metadata.")
        return errors

    def _link_omega_daily_phi(
        self,
        model: cp_model.CpModel,
        omega_daily: dict,
        phi: dict,
        index: object,
    ) -> int:
        """Define omega_daily = ∑_h phi_{d,w,h} for each (d, w)."""
        count = 0
        for (d_id, w), omega_var in omega_daily.items():
            terms = [
                phi[(d_id, w, h)]
                for h in index.periods
                if (d_id, w, h) in phi
            ]
            if terms:
                model.Add(omega_var == sum(terms))
                count += 1
        return count

    def _link_omega_daily_z_hat(
        self,
        model: cp_model.CpModel,
        omega_daily: dict,
        Z_hat: dict,
        index: object,
    ) -> int:
        """Define omega_daily = ∑_g ∑_h z_hat_{d,g,w,h} for each (d, w)."""
        G_d: dict = index.G_d
        count = 0
        for (d_id, w), omega_var in omega_daily.items():
            terms = [
                Z_hat[(d_id, g_id, w, h)]
                for g_id in G_d.get(d_id, [])
                for h in index.periods
                if (d_id, g_id, w, h) in Z_hat
            ]
            if terms:
                model.Add(omega_var == sum(terms))
                count += 1
        return count

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        omega_daily: dict = context.get_variable_group("omega_daily")
        index = context._metadata["index"]
        instructors_by_id: dict = index.instructors_by_id

        count = 0

        # Link omega_daily to actual teaching activity
        phi = context.get_variable_group("phi")
        Z_hat = context.get_variable_group("Z_hat")

        if phi is not None:
            count += self._link_omega_daily_phi(model, omega_daily, phi, index)
        elif Z_hat is not None:
            count += self._link_omega_daily_z_hat(model, omega_daily, Z_hat, index)
        # If neither exists, omega_daily must have been defined elsewhere

        # Upper-bound constraint
        for (d_id, w), omega_var in omega_daily.items():
            instructor = instructors_by_id.get(d_id)
            if instructor is None:
                continue
            model.Add(omega_var <= instructor.max_daily_periods)
            count += 1

        return count
