"""Validation interfaces and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")

__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "Validator",
    "ValidationPipelinePort",
]


@dataclass
class ValidationIssue:
    """A single validation error/warning, optionally pointing at an entity.

    ``entity_type``/``entity_id`` let the UI deep-link the issue to the
    screen where it can be fixed (e.g. entity_type="instructor" ->
    /docentes?q=<name>). Both are ``None`` for aggregate/system-wide issues
    that don't correspond to a single record.
    """

    message: str
    entity_type: str | None = None
    entity_id: str | None = None
    entity_label: str | None = None


@dataclass
class ValidationResult:
    """Outcome of a validation pass."""

    is_valid: bool = True
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def add_error(
        self,
        msg: str,
        entity_type: str | None = None,
        entity_id: object | None = None,
        entity_label: str | None = None,
    ) -> None:
        """Record a validation error and mark result as invalid."""
        self.errors.append(
            ValidationIssue(msg, entity_type, str(entity_id) if entity_id is not None else None, entity_label),
        )
        self.is_valid = False

    def add_warning(
        self,
        msg: str,
        entity_type: str | None = None,
        entity_id: object | None = None,
        entity_label: str | None = None,
    ) -> None:
        """Record a non-blocking warning."""
        self.warnings.append(
            ValidationIssue(msg, entity_type, str(entity_id) if entity_id is not None else None, entity_label),
        )

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
        return cls(is_valid=False, errors=[ValidationIssue(error)])


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
