"""Stores solver results back into the database through domain entities.

Converts OptimizationResult (solver output) into domain Assignment and
SessionBlock entities, updates the ScheduleRun with comprehensive
statistics, and persists everything through the Unit of Work.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.logging.logger import get_logger
from app.core.utils.types import EntityId, generate_id

if TYPE_CHECKING:
    from app.domain.interfaces.unit_of_work import UnitOfWork
    from app.solver.result import (
        AssignmentResult,
        OptimizationResult,
        SolverStatistics,
    )

__all__ = ["ResultPublisher"]

_logger = get_logger(__name__)


class ResultPublisher:
    """Converts solver output into domain entities and persists them."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def publish(
        self,
        result: OptimizationResult,
        run_id: EntityId,
    ) -> None:
        """Persist solver results and update the schedule run."""
        with self._uow:
            self._update_run_status(result, run_id)
            if result.is_feasible:
                self._persist_assignments(result.assignments, run_id)
            self._uow.commit()

        _logger.info(
            "Published results for run %s — status=%s, assignments=%d",
            run_id, result.status.value, len(result.assignments),
        )

    def _update_run_status(
        self,
        result: OptimizationResult,
        run_id: EntityId,
    ) -> None:
        """Update the ScheduleRun with final status and comprehensive statistics."""
        run = self._uow.schedule_runs.get_by_id(run_id)
        if run is None:
            return

        run.status = result.status.value
        run.completed_at = datetime.now(timezone.utc)

        if result.statistics is not None:
            run.objective_value = result.statistics.objective_value
            run.gap = result.statistics.gap
            run.statistics = self._build_statistics_dict(result.statistics)

        if result.solver_config is not None:
            run.solver_config = {
                "max_time_seconds": result.solver_config.max_time_seconds,
                "num_workers": result.solver_config.num_workers,
                "gap_tolerance": result.solver_config.gap_tolerance,
            }

        if result.errors:
            run.statistics = {
                **run.statistics,
                "errors": result.errors,
            }

        self._uow.schedule_runs.save(run)

    @staticmethod
    def _build_statistics_dict(stats: SolverStatistics) -> dict:
        """Serialize all SolverStatistics fields into a JSON-safe dict."""
        return {
            "groups_total": stats.groups_total,
            "groups_scheduled": stats.groups_scheduled,
            "instructors_total": stats.instructors_total,
            "rooms_total": stats.rooms_total,
            "time_slots_total": stats.time_slots_total,
            "num_variables": stats.num_variables,
            "num_constraints": stats.num_constraints,
            "variables_by_category": stats.variables_by_category,
            "constraints_by_type": stats.constraints_by_type,
            "hard_constraints_total": stats.hard_constraints_total,
            "soft_constraints_total": stats.soft_constraints_total,
            "elapsed_seconds": stats.elapsed_seconds,
            "timings": stats.timings,
            "memory_usage_mb": stats.memory_usage_mb,
            "objective_value": stats.objective_value,
            "gap": stats.gap,
            "workload_spread": stats.workload_spread,
            "avg_preference_score": stats.avg_preference_score,
            "room_utilization_pct": stats.room_utilization_pct,
        }

    def _persist_assignments(
        self,
        assignments: list[AssignmentResult],
        run_id: EntityId,
    ) -> None:
        """Create Assignment and SessionBlock entities from solver output."""
        from app.domain.entities.schedule import Assignment, SessionBlock

        for assignment_result in assignments:
            assignment = Assignment(
                id=generate_id(),
                schedule_run_id=run_id,
                group_id=assignment_result.group_id,
                instructor_id=assignment_result.instructor_id,
            )
            saved_assignment = self._uow.assignments.save(assignment)

            for session in assignment_result.sessions:
                block = SessionBlock(
                    id=generate_id(),
                    assignment_id=saved_assignment.id,
                    block_index=session.block_index,
                    day_of_week=session.day_of_week,
                    start_period=session.start_period,
                    duration=session.duration,
                    classroom_id=session.classroom_id,
                )
                self._uow.session_blocks.save(block)
