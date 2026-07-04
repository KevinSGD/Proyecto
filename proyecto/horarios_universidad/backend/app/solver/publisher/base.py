"""Abstract result publisher."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.utils.types import EntityId
from app.solver.result import OptimizationResult

__all__ = ["AbstractPublisher"]


class AbstractPublisher(ABC):
    """Persists an optimization result."""

    @abstractmethod
    def publish(self, result: OptimizationResult, run_id: EntityId) -> None:
        """Write *result* to persistent storage under *run_id*."""
        ...
