"""Abstract interfaces for the solver pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.utils.types import EntityId

__all__ = [
    "SolverPort",
    "ConstraintPort",
    "ObjectivePort",
    "LoaderPort",
    "ExtractorPort",
    "PublisherPort",
]


class SolverPort(ABC):
    """Main solver interface for schedule optimization."""

    @abstractmethod
    def solve(
        self, problem: OptimizationProblem,
    ) -> OptimizationResult: ...


class ConstraintPort(ABC):
    """Interface for a single constraint applied during optimization."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def constraint_type(self) -> str:
        """Return 'hard' or 'soft'."""
        return "hard"

    @property
    def is_enabled(self) -> bool:
        """Whether this constraint is active."""
        return True

    @abstractmethod
    def apply(self, context: OptimizationContext) -> None: ...


class ObjectivePort(ABC):
    """Interface for an objective component in the optimization model."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def weight(self) -> int:
        """Relative weight of this objective component."""
        return 1

    @abstractmethod
    def compute_terms(
        self, context: OptimizationContext,
    ) -> list[tuple]: ...


class LoaderPort(ABC):
    """Loads institution data into solver-ready format."""

    @abstractmethod
    def load(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> OptimizationProblem: ...


class ExtractorPort(ABC):
    """Extracts a solution from the solved optimization context."""

    @abstractmethod
    def extract(
        self, context: OptimizationContext,
    ) -> OptimizationResult: ...


class PublisherPort(ABC):
    """Publishes optimization results to persistent storage."""

    @abstractmethod
    def publish(
        self, result: OptimizationResult, run_id: EntityId,
    ) -> None: ...
