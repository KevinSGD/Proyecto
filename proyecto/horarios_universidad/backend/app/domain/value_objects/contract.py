"""Contract and workload value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.exceptions.base import DomainError

__all__ = [
    "ContractType",
    "WorkloadLimits",
]


class ContractType(Enum):
    """Types of instructor employment contracts."""

    FULL_TIME = "full_time"
    HALF_TIME = "half_time"
    ADJUNCT = "adjunct"
    VISITING = "visiting"
    HOURLY = "hourly"


@dataclass(frozen=True)
class WorkloadLimits:
    """Workload constraints derived from a contract type."""

    max_daily_periods: int
    max_weekly_periods: int
    min_weekly_periods: int = 0
    max_days: int | None = None

    def __post_init__(self) -> None:
        if self.max_daily_periods <= 0:
            raise DomainError(
                f"max_daily_periods must be > 0, got {self.max_daily_periods}"
            )
        if self.max_weekly_periods <= 0:
            raise DomainError(
                f"max_weekly_periods must be > 0, got {self.max_weekly_periods}"
            )
        if self.min_weekly_periods > self.max_weekly_periods:
            raise DomainError(
                f"min_weekly_periods ({self.min_weekly_periods}) must be "
                f"<= max_weekly_periods ({self.max_weekly_periods})"
            )
