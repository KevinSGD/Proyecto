"""Stores solver results back into the database through domain entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.utils.types import EntityId, generate_id

if TYPE_CHECKING:
    from app.domain.interfaces.unit_of_work import UnitOfWork
    from app.solver.result import AssignmentResult, OptimizationResult

__all__ = ["ResultPublisher"]


class ResultPublisher:
    """Converts solver output into domain entities and persists them."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def publish(
        self,
        result: OptimizationResult,
        run_id: EntityId,
    ) -> None:
        with self._uow:
            self._update_run_status(result, run_id)
            if result.is_feasible:
                self._persist_assignments(result.assignments, run_id)
            self._uow.commit()

    def _update_run_status(
        self,
        result: OptimizationResult,
        run_id: EntityId,
    ) -> None:
        run = self._uow.schedule_runs.get_by_id(run_id)
        if run is None:
            return

        run.status = result.status.value
        run.completed_at = datetime.now(timezone.utc)

        if result.statistics is not None:
            run.objective_value = result.statistics.objective_value
            run.gap = result.statistics.gap
            run.statistics = {
                "groups_total": result.statistics.groups_total,
                "groups_scheduled": result.statistics.groups_scheduled,
                "instructors_total": result.statistics.instructors_total,
                "rooms_total": result.statistics.rooms_total,
                "elapsed_seconds": result.statistics.elapsed_seconds,
                "num_variables": result.statistics.num_variables,
                "num_constraints": result.statistics.num_constraints,
            }

        if result.solver_config is not None:
            run.solver_config = {
                "max_time_seconds": result.solver_config.max_time_seconds,
                "num_workers": result.solver_config.num_workers,
                "gap_tolerance": result.solver_config.gap_tolerance,
            }

        self._uow.schedule_runs.save(run)

    def _persist_assignments(
        self,
        assignments: list[AssignmentResult],
        run_id: EntityId,
    ) -> None:
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
