"""Exception hierarchy for the scheduler system."""

from app.core.exceptions.base import (
    CompositeValidationError,
    ConfigurationError,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    ExportError,
    FieldValidationError,
    ImportError_,
    InfeasibleError,
    InvalidStateError,
    OptimizationError,
    RepositoryError,
    SchedulerError,
    SolverConfigError,
    TimeoutError_,
    ValidationError,
)

__all__ = [
    "CompositeValidationError",
    "ConfigurationError",
    "DomainError",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "ExportError",
    "FieldValidationError",
    "ImportError_",
    "InfeasibleError",
    "InvalidStateError",
    "OptimizationError",
    "RepositoryError",
    "SchedulerError",
    "SolverConfigError",
    "TimeoutError_",
    "ValidationError",
]
