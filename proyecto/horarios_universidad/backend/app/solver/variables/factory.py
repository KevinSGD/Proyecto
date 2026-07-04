"""Decision and auxiliary variable factory — Doc 04 (decision) and Doc 05 (auxiliary)."""

from __future__ import annotations

from ortools.sat.python import cp_model

from app.core.logging.logger import get_logger
from app.core.utils.types import EntityId
from app.solver.context import OptimizationContext, OptimizationProblem
from app.solver.preprocessing.index_builder import IndexData

__all__ = ["VariableFactory"]

_logger = get_logger(__name__)


def _sid(entity_id: EntityId) -> str:
    """Short 8-char hex prefix for variable names."""
    return str(entity_id)[:8]


class VariableFactory:
    """Creates and registers all CP-SAT variables into the OptimizationContext."""

    def create_all(
        self,
        model: cp_model.CpModel,
        problem: OptimizationProblem,
        index: IndexData,
        context: OptimizationContext,
    ) -> None:
        """Create every variable group defined in Doc 04 and Doc 05."""
        self._create_decision_variables(model, index, context)
        self._create_auxiliary_variables(model, problem, index, context)
        total = sum(
            len(v) if isinstance(v, dict) else 1
            for v in context.variables.values()
        )
        _logger.info("Variable factory: %d variable objects created", total)

    # ------------------------------------------------------------------
    # Doc 04 — Decision variables
    # ------------------------------------------------------------------

    def _create_decision_variables(
        self,
        model: cp_model.CpModel,
        index: IndexData,
        context: OptimizationContext,
    ) -> None:
        X: dict[tuple[EntityId, EntityId], cp_model.IntVar] = {}
        for gid, d_list in index.D_g.items():
            for did in d_list:
                name = f"x_assign_d{_sid(did)}_g{_sid(gid)}"
                X[(did, gid)] = model.NewBoolVar(name)
        context.add_variable_group("X", X)

        Y: dict[tuple[EntityId, int, int, int, EntityId], cp_model.IntVar] = {}
        for gid, group in index.groups_by_id.items():
            for l_idx in range(group.num_blocks):
                starts = index.T_g_l_ini.get((gid, l_idx), [])
                for w, h in starts:
                    for aid in index.A_g.get(gid, []):
                        name = f"y_start_g{_sid(gid)}_l{l_idx}_w{w}_h{h}_a{_sid(aid)}"
                        Y[(gid, l_idx, w, h, aid)] = model.NewBoolVar(name)
        context.add_variable_group("Y", Y)

        Z: dict[tuple[EntityId, int, int, EntityId], cp_model.IntVar] = {}
        for gid in index.groups_by_id:
            eligible = index.T_g.get(gid, set())
            for w, h in eligible:
                for aid in index.A_g.get(gid, []):
                    name = f"z_cover_g{_sid(gid)}_w{w}_h{h}_a{_sid(aid)}"
                    Z[(gid, w, h, aid)] = model.NewBoolVar(name)
        context.add_variable_group("Z", Z)

    # ------------------------------------------------------------------
    # Doc 05 — Auxiliary variables
    # ------------------------------------------------------------------

    def _create_auxiliary_variables(
        self,
        model: cp_model.CpModel,
        problem: OptimizationProblem,
        index: IndexData,
        context: OptimizationContext,
    ) -> None:
        days = index.days
        ppd = problem.time_config.periods_per_day if problem.time_config else 1

        omega: dict[EntityId, cp_model.IntVar] = {}
        omega_daily: dict[tuple[EntityId, int], cp_model.IntVar] = {}
        delta: dict[tuple[EntityId, int], cp_model.IntVar] = {}
        n_days: dict[EntityId, cp_model.IntVar] = {}
        phi: dict[tuple[EntityId, int, int], cp_model.IntVar] = {}
        first_slot: dict[tuple[EntityId, int], cp_model.IntVar] = {}
        last_slot: dict[tuple[EntityId, int], cp_model.IntVar] = {}
        span: dict[tuple[EntityId, int], cp_model.IntVar] = {}
        gaps: dict[tuple[EntityId, int], cp_model.IntVar] = {}
        R_room: dict[tuple[EntityId, EntityId], cp_model.IntVar] = {}

        for instructor in problem.instructors:
            did = instructor.id
            sid = _sid(did)

            omega[did] = model.NewIntVar(
                0, instructor.max_weekly_periods, f"omega_d{sid}"
            )
            n_days[did] = model.NewIntVar(0, len(days), f"n_days_d{sid}")

            for w in days:
                omega_daily[(did, w)] = model.NewIntVar(
                    0, instructor.max_daily_periods, f"omega_daily_d{sid}_w{w}"
                )
                delta[(did, w)] = model.NewBoolVar(f"delta_d{sid}_w{w}")
                first_slot[(did, w)] = model.NewIntVar(1, ppd, f"first_d{sid}_w{w}")
                last_slot[(did, w)] = model.NewIntVar(1, ppd, f"last_d{sid}_w{w}")
                span[(did, w)] = model.NewIntVar(0, ppd, f"span_d{sid}_w{w}")
                gaps[(did, w)] = model.NewIntVar(0, ppd, f"gaps_d{sid}_w{w}")

                for h in range(1, ppd + 1):
                    phi[(did, w, h)] = model.NewBoolVar(f"phi_d{sid}_w{w}_h{h}")

        all_instr_ids = [i.id for i in problem.instructors]
        max_wkly = max((i.max_weekly_periods for i in problem.instructors), default=0)
        omega_max_var = model.NewIntVar(0, max_wkly, "omega_max")
        omega_min_var = model.NewIntVar(0, max_wkly, "omega_min")

        for group in problem.groups:
            gid = group.id
            for aid in index.A_g.get(gid, []):
                name = f"r_room_g{_sid(gid)}_a{_sid(aid)}"
                R_room[(gid, aid)] = model.NewBoolVar(name)

        context.add_variable_group("omega", omega)
        context.add_variable_group("omega_daily", omega_daily)
        context.add_variable_group("delta", delta)
        context.add_variable_group("n_days", n_days)
        context.add_variable_group("omega_max", omega_max_var)
        context.add_variable_group("omega_min", omega_min_var)
        context.add_variable_group("R_room", R_room)
        context.add_variable_group("phi", phi)
        context.add_variable_group("first_slot", first_slot)
        context.add_variable_group("last_slot", last_slot)
        context.add_variable_group("span", span)
        context.add_variable_group("gaps", gaps)
