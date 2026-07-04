"""Abstract data loader for the solver."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.utils.types import EntityId
from app.solver.context import OptimizationProblem

__all__ = ["AbstractLoader"]


class AbstractLoader(ABC):
    """Loads domain data and builds an OptimizationProblem."""

    @abstractmethod
    def load(
        self, institution_id: EntityId, period_id: EntityId
    ) -> OptimizationProblem:
        """Fetch all data needed for a solver run and return the problem."""
        ...
