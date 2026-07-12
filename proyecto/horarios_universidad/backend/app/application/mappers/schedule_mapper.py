"""Entity-to-DTO mappers for schedule and solver result entities."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.entities.import_export import ValidationReport
    from app.domain.entities.schedule import Assignment, ScheduleRun, SessionBlock


def schedule_run_to_dict(entity: ScheduleRun) -> dict[str, Any]:
    """Map a ScheduleRun entity to a flat dictionary."""
    return asdict(entity)


def assignment_to_dict(entity: Assignment) -> dict[str, Any]:
    """Map an Assignment entity to a flat dictionary."""
    return asdict(entity)


def session_block_to_dict(entity: SessionBlock) -> dict[str, Any]:
    """Map a SessionBlock entity to a flat dictionary."""
    return asdict(entity)


def assignment_detail_to_dict(
    assignment: Assignment,
    sessions: list[SessionBlock],
) -> dict[str, Any]:
    """Map an Assignment and its SessionBlocks into a detail dictionary."""
    data = asdict(assignment)
    data["sessions"] = [asdict(s) for s in sessions]
    return data


def schedule_run_detail_to_dict(
    run: ScheduleRun,
    assignments_with_sessions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Map a ScheduleRun with nested assignments into a detail dictionary."""
    data = asdict(run)
    data["assignments"] = assignments_with_sessions
    return data


def validation_report_to_dict(entity: ValidationReport) -> dict[str, Any]:
    """Map a ValidationReport entity to a flat dictionary."""
    return asdict(entity)
