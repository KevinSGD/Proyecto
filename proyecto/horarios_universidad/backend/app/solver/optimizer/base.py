"""Abstract optimizer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.solver.config import SolverConfiguration
from app.solver.context import OptimizationContext
from app.solver.result import OptimizationResult

__all__ = ["AbstractOptimizer"]


class AbstractOptimizer(ABC):
    """Drives the actual solve process."""

    @abstractmethod
    def optimize(self, context: OptimizationContext) -> OptimizationResult:
        """Run the solver on the prepared context."""
        ...

    @abstractmethod
    def configure(self, config: SolverConfiguration) -> None:
        """Apply solver-specific settings before the run."""
        ...
