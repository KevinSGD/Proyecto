"""Derived sets and index structures — Doc 02 Section 4, Doc 09 Module 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId
from app.solver.context import OptimizationProblem, SolverClassroom, SolverGroup, SolverInstructor

__all__ = ["IndexData", "build_indices"]


@dataclass
class IndexData:
    """All derived sets and reverse-index maps built from OptimizationProblem."""

    groups_by_id: dict[EntityId, SolverGroup] = field(default_factory=dict)
    instructors_by_id: dict[EntityId, SolverInstructor] = field(default_factory=dict)
    classrooms_by_id: dict[EntityId, SolverClassroom] = field(default_factory=dict)

    # D_g: candidate instructors per group
    D_g: dict[EntityId, list[EntityId]] = field(default_factory=dict)
    # A_g: compatible classrooms per group
    A_g: dict[EntityId, list[EntityId]] = field(default_factory=dict)
    # G_d: groups per instructor (inverse of D_g)
    G_d: dict[EntityId, list[EntityId]] = field(default_factory=dict)

    # T_g: eligible (day, period) slots per group
    T_g: dict[EntityId, set[tuple[int, int]]] = field(default_factory=dict)
    # T_g_l_ini: valid start slots per (group_id, block_index)
    T_g_l_ini: dict[tuple[EntityId, int], list[tuple[int, int]]] = field(default_factory=dict)
    # coverage: slots covered by starting block l of group g at (w, h_start)
    coverage: dict[tuple[EntityId, int, int, int], list[tuple[int, int]]] = field(default_factory=dict)

    days: list[int] = field(default_factory=list)
    periods: list[int] = field(default_factory=list)
    all_slots: list[tuple[int, int]] = field(default_factory=list)


def _build_all_slots(days: list[int], periods: list[int]) -> list[tuple[int, int]]:
    return [(w, h) for w in days for h in periods]


def _build_T_g_l_ini(
    group: SolverGroup,
    eligible: set[tuple[int, int]],
    periods_per_day: int,
) -> dict[int, list[tuple[int, int]]]:
    """Return {block_index: [valid_start_slots]} for one group."""
    result: dict[int, list[tuple[int, int]]] = {}
    for l_idx, dur in enumerate(group.block_durations):
        valid: list[tuple[int, int]] = []
        for w, h in eligible:
            if h + dur - 1 > periods_per_day:
                continue
            covered = {(w, h + offset) for offset in range(dur)}
            if covered.issubset(eligible):
                valid.append((w, h))
        result[l_idx] = valid
    return result


def _build_coverage(
    group_id: EntityId,
    block_durations: tuple[int, ...],
    t_g_l_ini: dict[int, list[tuple[int, int]]],
) -> dict[tuple[EntityId, int, int, int], list[tuple[int, int]]]:
    """Return coverage map for all valid starts of all blocks of one group."""
    cov: dict[tuple[EntityId, int, int, int], list[tuple[int, int]]] = {}
    for l_idx, dur in enumerate(block_durations):
        for w, h in t_g_l_ini.get(l_idx, []):
            key = (group_id, l_idx, w, h)
            cov[key] = [(w, h + offset) for offset in range(dur)]
    return cov


def build_indices(problem: OptimizationProblem) -> IndexData:
    """Construct all derived index structures from the optimisation problem."""
    index = IndexData()

    index.groups_by_id = {g.id: g for g in problem.groups}
    index.instructors_by_id = {i.id: i for i in problem.instructors}
    index.classrooms_by_id = {c.id: c for c in problem.classrooms}

    tc = problem.time_config
    if tc is not None:
        index.days = list(tc.days)
        index.periods = list(range(1, tc.periods_per_day + 1))
    else:
        index.days = []
        index.periods = []

    index.all_slots = _build_all_slots(index.days, index.periods)
    all_slots_set: set[tuple[int, int]] = set(index.all_slots)
    ppd = tc.periods_per_day if tc is not None else 0

    for group in problem.groups:
        gid = group.id
        index.D_g[gid] = list(group.candidate_instructors)
        index.A_g[gid] = list(group.compatible_classrooms)
        index.T_g[gid] = set(all_slots_set)

        t_g_l_ini_map = _build_T_g_l_ini(group, index.T_g[gid], ppd)
        for l_idx, starts in t_g_l_ini_map.items():
            index.T_g_l_ini[(gid, l_idx)] = starts

        index.coverage.update(_build_coverage(gid, group.block_durations, t_g_l_ini_map))

    # G_d: inverse mapping of D_g
    for gid, instructors in index.D_g.items():
        for did in instructors:
            index.G_d.setdefault(did, []).append(gid)

    return index
