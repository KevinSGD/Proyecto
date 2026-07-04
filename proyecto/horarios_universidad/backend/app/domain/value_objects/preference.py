"""Preference and priority value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.exceptions.base import DomainError

__all__ = [
    "PreferenceScore",
    "Priority",
    "Weight",
]


@dataclass(frozen=True)
class PreferenceScore:
    """A bounded preference score."""

    value: int
    max_value: int = 10

    def __post_init__(self) -> None:
        if not 0 <= self.value <= self.max_value:
            raise DomainError(
                f"PreferenceScore must be between 0 and {self.max_value}, "
                f"got {self.value}"
            )


class Priority(Enum):
    """Priority levels for scheduling decisions."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass(frozen=True)
class Weight:
    """Non-negative weight for objective function terms."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise DomainError(
                f"Weight must be >= 0, got {self.value}"
            )
