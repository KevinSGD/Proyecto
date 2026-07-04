"""Abstract solver validator."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.interfaces.validation import ValidationResult
from app.solver.context import OptimizationProblem

__all__ = ["AbstractSolverValidator"]


class AbstractSolverValidator(ABC):
    """Base class for pre-solve data validators."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def validate(self, problem: OptimizationProblem) -> ValidationResult:
        """Validate *problem* and return the result."""
        ...
