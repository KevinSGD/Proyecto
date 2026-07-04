"""HD-04: Consistencia docente-sesión (ẑ y φ) — Doc 06, Section HD-04."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext


class Hd04TeacherSessionConsistency(AbstractConstraint):
    """Creates ẑ_{d,g,w,h} via McCormick linearisation and derives φ_{d,w,h}."""

    @property
    def info(self) -> ConstraintInfo:
        return ConstraintInfo(
            name="HD-04",
            description=(
                "McCormick linearisation ẑ_{d,g,w,h} = X_{d,g} * z_agg_{g,w,h}; "
                "derives φ_{d,w,h} = ∑_g ẑ_{d,g,w,h}. "
                "Registers 'Z_hat' and updates 'phi' in context."
            ),
            constraint_type="hard",
            math_reference="HD-04",
            module_path="constraints.hard.hd04_teacher_session_consistency",
        )

    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        errors: list[str] = []
        for name in ("X", "Z", "phi"):
            if context.get_variable_group(name) is None:
                errors.append(f"HD-04: variable group '{name}' is not registered.")
        if context._metadata.get("index") is None:
            errors.append("HD-04: 'index' not found in context metadata.")
        return errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_z_agg(
        self,
        model: cp_model.CpModel,
        Z: dict,
        g_id: object,
        w: int,
        h: int,
        rooms: list,
    ) -> cp_model.IntVar | None:
        """Aggregate Z over rooms for (g, w, h). Returns None if no Z exists."""
        z_keys = [(g_id, w, h, a_id) for a_id in rooms if (g_id, w, h, a_id) in Z]
        if not z_keys:
            return None
        if len(z_keys) == 1:
            return Z[z_keys[0]]
        # Multiple rooms — sum should be ≤ 1 (enforced by HD-06), but use IntVar
        z_sum = model.NewBoolVar(f"zagg_g{g_id}_w{w}_h{h}")
        model.AddMaxEquality(z_sum, [Z[k] for k in z_keys])
        return z_sum

    def _make_z_hat(
        self,
        model: cp_model.CpModel,
        x_var: cp_model.IntVar,
        z_agg: cp_model.IntVar,
        label: str,
    ) -> cp_model.IntVar:
        """McCormick BoolVar for x_var AND z_agg."""
        z_hat = model.NewBoolVar(label)
        model.Add(z_hat <= x_var)
        model.Add(z_hat <= z_agg)
        model.Add(z_hat >= x_var + z_agg - 1)
        return z_hat

    # ------------------------------------------------------------------

    def apply(self, context: OptimizationContext) -> int:
        model: cp_model.CpModel = context.model
        X: dict = context.get_variable_group("X")
        Z: dict = context.get_variable_group("Z")
        phi: dict = context.get_variable_group("phi")
        index = context._metadata["index"]

        G_d: dict = index.G_d
        A_g: dict = index.A_g
        T_g: dict = index.T_g

        Z_hat: dict = {}
        # Accumulate z_hat contributions for phi per (d, w, h)
        phi_terms: dict[tuple, list] = {}

        count = 0

        for d_id, group_ids in G_d.items():
            for g_id in group_ids:
                x_key = (d_id, g_id)
                if x_key not in X:
                    continue
                x_var = X[x_key]
                rooms = A_g.get(g_id, [])

                for (w, h) in T_g.get(g_id, set()):
                    z_agg = self._build_z_agg(model, Z, g_id, w, h, rooms)
                    if z_agg is None:
                        continue

                    label = f"zhat_d{d_id}_g{g_id}_w{w}_h{h}"
                    z_hat_var = self._make_z_hat(model, x_var, z_agg, label)
                    Z_hat[(d_id, g_id, w, h)] = z_hat_var
                    count += 3  # three McCormick constraints

                    phi_key = (d_id, w, h)
                    phi_terms.setdefault(phi_key, []).append(z_hat_var)

        # Link phi to z_hat sums (HD-05 ensures at most 1, so sum == phi)
        for (d_id, w, h), terms in phi_terms.items():
            p_key = (d_id, w, h)
            if p_key not in phi:
                continue
            model.Add(phi[p_key] == sum(terms))
            count += 1

        context.add_variable_group("Z_hat", Z_hat)
        return count
