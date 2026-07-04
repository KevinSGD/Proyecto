"""Validation interfaces and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")

__all__ = [
    "ValidationResult",
    "Validator",
    "ValidationPipelinePort",
]


@dataclass
class ValidationResult:
    """Outcome of a validation pass."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Record a validation error and mark result as invalid."""
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        """Record a non-blocking warning."""
        self.warnings.append(msg)

    def merge(self, other: ValidationResult) -> None:
        """Absorb errors and warnings from another result."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False

    @classmethod
    def ok(cls) -> ValidationResult:
        """Create a passing validation result."""
        return cls(is_valid=True)

    @classmethod
    def fail(cls, error: str) -> ValidationResult:
        """Create a failing validation result with a single error."""
        return cls(is_valid=False, errors=[error])


class Validator(ABC, Generic[T]):
    """Abstract validator for a specific data type."""

    @abstractmethod
    def validate(self, data: T) -> ValidationResult: ...


class ValidationPipelinePort(ABC):
    """Ordered pipeline of validators."""

    @abstractmethod
    def add_validator(self, validator: Validator[Any]) -> None: ...

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult: ...
