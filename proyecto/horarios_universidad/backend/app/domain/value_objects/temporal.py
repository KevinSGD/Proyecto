"""Temporal value objects for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.exceptions.base import DomainError

__all__ = [
    "DayOfWeek",
    "TimeSlot",
    "TimeRange",
    "SessionPattern",
    "ScheduleTypeName",
]


class DayOfWeek(Enum):
    """Days of the week with ISO numbering."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass(frozen=True)
class TimeSlot:
    """A single time slot defined by day and period."""

    day: DayOfWeek
    period: int

    def __post_init__(self) -> None:
        if self.period < 1:
            raise DomainError(
                f"TimeSlot period must be >= 1, got {self.period}"
            )


@dataclass(frozen=True)
class TimeRange:
    """A contiguous range of periods within a day."""

    start_period: int
    end_period: int

    def __post_init__(self) -> None:
        if self.start_period >= self.end_period:
            raise DomainError(
                f"TimeRange start ({self.start_period}) must be "
                f"less than end ({self.end_period})"
            )


@dataclass(frozen=True)
class SessionPattern:
    """Describes how credit hours are split into session blocks."""

    credit_hours: int
    num_blocks: int
    block_durations: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.block_durations) != self.num_blocks:
            raise DomainError(
                f"block_durations length ({len(self.block_durations)}) "
                f"must equal num_blocks ({self.num_blocks})"
            )
        if sum(self.block_durations) <= 0:
            raise DomainError(
                "Sum of block_durations must be greater than 0"
            )


class ScheduleTypeName(Enum):
    """Named schedule types (shifts)."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    MIXED = "mixed"
    WEEKEND = "weekend"
