"""Abstract solution extractor."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.solver.context import OptimizationContext
from app.solver.result import OptimizationResult

__all__ = ["AbstractExtractor"]


class AbstractExtractor(ABC):
    """Extracts a domain-level result from a solved optimization context."""

    @abstractmethod
    def extract(self, context: OptimizationContext) -> OptimizationResult:
        """Read variable values from *context* and build the result."""
        ...
