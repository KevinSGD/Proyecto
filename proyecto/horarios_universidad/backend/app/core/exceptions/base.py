"""Exception hierarchy for the scheduler system."""

from __future__ import annotations

from typing import Any


class SchedulerError(Exception):
    """Base exception for all scheduler errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DomainError(SchedulerError):
    """A domain rule was violated."""


class EntityNotFoundError(DomainError):
    """An entity could not be found by its identifier."""

    def __init__(self, *, entity_type: str, entity_id: str | int,
                 message: str | None = None) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(message or f"{entity_type} with id '{entity_id}' not found")


class DuplicateEntityError(DomainError):
    """An entity with the same identity already exists."""

    def __init__(self, *, entity_type: str, entity_id: str | int,
                 message: str | None = None) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(message or f"{entity_type} with id '{entity_id}' already exists")


class InvalidStateError(DomainError):
    """An entity is in a state that prevents the requested operation."""

    def __init__(self, *, entity_type: str, current_state: str,
                 expected_state: str, message: str | None = None) -> None:
        self.entity_type = entity_type
        self.current_state = current_state
        self.expected_state = expected_state
        msg = message or f"{entity_type} is in state '{current_state}', expected '{expected_state}'"
        super().__init__(msg)


class ValidationError(SchedulerError):
    """Input validation failed."""


class FieldValidationError(ValidationError):
    """A single field failed validation."""

    def __init__(self, *, field_name: str, value: Any, reason: str) -> None:
        self.field_name = field_name
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field_name}': {reason}")


class CompositeValidationError(ValidationError):
    """Multiple validation errors occurred."""

    def __init__(self, *, errors: list[ValidationError]) -> None:
        self.errors = errors
        count = len(errors)
        summary = "; ".join(e.message for e in errors[:5])
        suffix = f" (+{count - 5} more)" if count > 5 else ""
        super().__init__(f"{count} validation error(s): {summary}{suffix}")


class OptimizationError(SchedulerError):
    """An error occurred during the optimization process."""


class InfeasibleError(OptimizationError):
    """The solver could not find a feasible solution."""

    def __init__(self, *, message: str = "No feasible solution exists for the given constraints",
                 conflicting_constraints: list[str] | None = None) -> None:
        self.conflicting_constraints = conflicting_constraints or []
        super().__init__(message)


class TimeoutError_(OptimizationError):
    """The solver exceeded its time budget."""

    def __init__(self, *, elapsed_seconds: float, best_objective: float | None = None) -> None:
        self.elapsed_seconds = elapsed_seconds
        self.best_objective = best_objective
        obj_info = f", best objective: {best_objective}" if best_objective is not None else ""
        super().__init__(f"Solver timed out after {elapsed_seconds:.1f}s{obj_info}")



class ConfigurationError(SchedulerError):
    """Application configuration is missing or invalid."""


class ImportError_(SchedulerError):
    """An error occurred while importing external data."""

    def __init__(self, *, source: str, reason: str, row: int | None = None) -> None:
        self.source = source
        self.reason = reason
        self.row = row
        location = f" at row {row}" if row is not None else ""
        super().__init__(f"Import from '{source}' failed{location}: {reason}")


class ExportError(SchedulerError):
    """An error occurred while exporting data."""

    def __init__(self, *, target: str, reason: str) -> None:
        self.target = target
        self.reason = reason
        super().__init__(f"Export to '{target}' failed: {reason}")


class RepositoryError(SchedulerError):
    """An error occurred while accessing the data store."""
