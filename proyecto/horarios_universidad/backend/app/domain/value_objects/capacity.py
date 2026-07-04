"""Capacity and enrollment value objects."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions.base import DomainError

__all__ = [
    "Capacity",
    "Enrollment",
    "is_compatible",
]


@dataclass(frozen=True)
class Capacity:
    """Physical capacity of a classroom."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise DomainError(
                f"Capacity must be >= 1, got {self.value}"
            )


@dataclass(frozen=True)
class Enrollment:
    """Expected student enrollment for a group."""

    expected: int

    def __post_init__(self) -> None:
        if self.expected < 1:
            raise DomainError(
                f"Enrollment must be >= 1, got {self.expected}"
            )


def is_compatible(enrollment: Enrollment, capacity: Capacity) -> bool:
    """Check whether a classroom can accommodate the expected enrollment."""
    return enrollment.expected <= capacity.value
