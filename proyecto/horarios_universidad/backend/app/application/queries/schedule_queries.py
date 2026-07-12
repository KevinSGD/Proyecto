"""Read-side use cases for schedule runs and results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.application.exceptions.application_exceptions import (
    ResourceNotFoundError,
)
from app.application.mappers.schedule_mapper import (
    assignment_detail_to_dict,
    schedule_run_detail_to_dict,
    validation_report_to_dict,
)

if TYPE_CHECKING:
    from app.core.utils.types import EntityId
    from app.domain.entities.import_export import ValidationReport
    from app.domain.entities.schedule import ScheduleRun
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = [
    "GetScheduleRun",
    "ListScheduleRuns",
    "GetScheduleAssignments",
    "GetScheduleRunDetail",
    "GetValidationReport",
    "GetExecutionLogs",
]


class GetScheduleRun:
    """Retrieve a single schedule run by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, run_id: EntityId) -> ScheduleRun:
        with self._uow:
            run = self._uow.schedule_runs.get_by_id(run_id)
            if run is None:
                raise ResourceNotFoundError("ScheduleRun", run_id)
            return run


class ListScheduleRuns:
    """List all schedule runs for an institution + period pair."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> list[ScheduleRun]:
        with self._uow:
            return self._uow.schedule_runs.list_by_period(
                institution_id, period_id,
            )


class GetScheduleAssignments:
    """Return assignments with their session blocks for a schedule run."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, run_id: EntityId) -> list[dict[str, Any]]:
        with self._uow:
            run = self._uow.schedule_runs.get_by_id(run_id)
            if run is None:
                raise ResourceNotFoundError("ScheduleRun", run_id)

            assignments = self._uow.assignments.list_by_schedule_run(run_id)
            result: list[dict[str, Any]] = []
            for assignment in assignments:
                sessions = self._uow.session_blocks.list_by_assignment(
                    assignment.id,
                )
                result.append(
                    assignment_detail_to_dict(assignment, sessions),
                )
            return result


class GetScheduleRunDetail:
    """Return a schedule run together with all nested assignments and execution logs."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, run_id: EntityId) -> dict[str, Any]:
        from dataclasses import asdict

        with self._uow:
            run = self._uow.schedule_runs.get_by_id(run_id)
            if run is None:
                raise ResourceNotFoundError("ScheduleRun", run_id)

            assignments = self._uow.assignments.list_by_schedule_run(run_id)
            assignments_data: list[dict[str, Any]] = []
            for assignment in assignments:
                sessions = self._uow.session_blocks.list_by_assignment(
                    assignment.id,
                )
                assignments_data.append(
                    assignment_detail_to_dict(assignment, sessions),
                )

            logs = self._uow.execution_logs.list_by_run(run_id)
            detail = schedule_run_detail_to_dict(run, assignments_data)
            detail["execution_logs"] = [asdict(log) for log in logs]
            return detail


class GetValidationReport:
    """Retrieve a single validation report by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, report_id: EntityId) -> dict[str, Any]:
        with self._uow:
            report = self._uow.validation_reports.get_by_id(report_id)
            if report is None:
                raise ResourceNotFoundError("ValidationReport", report_id)
            return validation_report_to_dict(report)


class GetExecutionLogs:
    """Return execution event logs for a schedule run."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, run_id: EntityId) -> list[dict[str, Any]]:
        """Return all execution logs for the given run, ordered by timestamp."""
        from dataclasses import asdict

        with self._uow:
            run = self._uow.schedule_runs.get_by_id(run_id)
            if run is None:
                raise ResourceNotFoundError("ScheduleRun", run_id)
            logs = self._uow.execution_logs.list_by_run(run_id)
            return [asdict(log) for log in logs]
