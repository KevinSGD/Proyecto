"""Scheduling configuration entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "ScheduleType",
    "Group",
]


@dataclass
class ScheduleType:
    """Defines a named schedule shift (e.g. morning, afternoon)."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    schedule_type: str = ""
    active_days: list[int] = field(default_factory=list)
    start_period: int = 0
    end_period: int = 0
    slot_duration_minutes: int = 60


@dataclass
class Group:
    """A section/group of students for a specific subject offering."""

    id: EntityId = field(default_factory=generate_id)
    offering_line_id: EntityId = field(default_factory=generate_id)
    subject_id: EntityId = field(default_factory=generate_id)
    group_number: int = 0
    expected_enrollment: int = 0
    modality: str = ""
    schedule_type_id: EntityId = field(default_factory=generate_id)
    priority: int = 2
