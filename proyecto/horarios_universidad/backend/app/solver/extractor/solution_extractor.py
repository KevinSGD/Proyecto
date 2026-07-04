"""Solution extraction from CP-SAT variable values — Doc 09 Module 8."""

from __future__ import annotations

from typing import Any

from ortools.sat.python import cp_model

from app.core.logging.logger import get_logger
from app.core.utils.types import EntityId
from app.solver.context import OptimizationContext
from app.solver.extractor.base import AbstractExtractor
from app.solver.result import AssignmentResult, OptimizationResult, SessionResult, SolverStatus

__all__ = ["SolutionExtractor"]

_logger = get_logger(__name__)


class SolutionExtractor(AbstractExtractor):
    """Reads solved variable values and constructs domain-level AssignmentResult objects."""

    def extract(self, context: OptimizationContext) -> OptimizationResult:
        """Build an OptimizationResult by reading X and Y variable values."""
        solver: cp_model.CpSolver | None = context._metadata.get("solver")
        if solver is None:
            return OptimizationResult(
                status=SolverStatus.ERROR,
                errors=["No solver instance in context metadata"],
            )

        assignments = self._read_assignments(solver, context)
        status = context._metadata.get("solve_status", SolverStatus.FEASIBLE)
        return OptimizationResult(status=status, assignments=assignments)

    def extract_assignments(
        self, solver: cp_model.CpSolver, context: OptimizationContext
    ) -> list[AssignmentResult]:
        """Extract assignment list directly (called by CpSatOptimizer)."""
        return self._read_assignments(solver, context)

    def _read_assignments(
        self, solver: cp_model.CpSolver, context: OptimizationContext
    ) -> list[AssignmentResult]:
        X: dict = context.get_variable_group("X") or {}
        Y: dict = context.get_variable_group("Y") or {}
        index = context.index

        # Map group → assigned instructor (from X)
        group_instructor: dict[EntityId, EntityId] = {}
        for (did, gid), var in X.items():
            if solver.Value(var) == 1:
                group_instructor[gid] = did

        # Map group → list of sessions (from Y)
        group_sessions: dict[EntityId, list[SessionResult]] = {}
        for (gid, l_idx, w, h, aid), var in Y.items():
            if solver.Value(var) == 1:
                dur = 1
                if index is not None:
                    group = index.groups_by_id.get(gid)
                    if group and l_idx < len(group.block_durations):
                        dur = group.block_durations[l_idx]

                session = SessionResult(
                    block_index=l_idx,
                    day_of_week=w,
                    start_period=h,
                    duration=dur,
                    classroom_id=aid,
                )
                group_sessions.setdefault(gid, []).append(session)

        results: list[AssignmentResult] = []
        for gid, did in group_instructor.items():
            results.append(
                AssignmentResult(
                    group_id=gid,
                    instructor_id=did,
                    sessions=group_sessions.get(gid, []),
                )
            )

        _logger.info("Extracted %d group assignments from solution", len(results))
        return results
