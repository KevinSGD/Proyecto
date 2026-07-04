"""Schedule result and optimization execution entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "OptimizationConfig",
    "ScheduleRun",
    "Assignment",
    "SessionBlock",
    "ExecutionLog",
]


@dataclass
class OptimizationConfig:
    """Stored solver configuration for an institution/period."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId | None = None
    name: str = ""
    config_data: dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    created_at: datetime | None = None
    created_by: EntityId | None = None


@dataclass
class ScheduleRun:
    """A single execution of the schedule optimizer."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId = field(default_factory=generate_id)
    config_id: EntityId | None = None
    status: str = "pending"
    solver_config: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    objective_value: float | None = None
    gap: float | None = None
    created_by: EntityId | None = None


@dataclass
class Assignment:
    """Maps a group to an instructor within a schedule run."""

    id: EntityId = field(default_factory=generate_id)
    schedule_run_id: EntityId = field(default_factory=generate_id)
    group_id: EntityId = field(default_factory=generate_id)
    instructor_id: EntityId = field(default_factory=generate_id)


@dataclass
class SessionBlock:
    """A concrete time-and-room block for an assignment."""

    id: EntityId = field(default_factory=generate_id)
    assignment_id: EntityId = field(default_factory=generate_id)
    block_index: int = 0
    day_of_week: int = 0
    start_period: int = 0
    duration: int = 0
    classroom_id: EntityId = field(default_factory=generate_id)


@dataclass
class ExecutionLog:
    """Detailed event log for a solver run."""

    id: EntityId = field(default_factory=generate_id)
    schedule_run_id: EntityId = field(default_factory=generate_id)
    event_type: str = ""
    message: str = ""
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
