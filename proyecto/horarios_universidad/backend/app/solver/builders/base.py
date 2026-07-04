"""Abstract model builder."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.solver.context import OptimizationContext, OptimizationProblem

__all__ = ["AbstractModelBuilder"]


class AbstractModelBuilder(ABC):
    """Translates an OptimizationProblem into a solver-specific model."""

    @abstractmethod
    def build(self, problem: OptimizationProblem) -> OptimizationContext:
        """Create decision variables and return a ready-to-constrain context."""
        ...
