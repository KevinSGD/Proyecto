"""Abstract objective component."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = [
    "ObjectiveInfo",
    "AbstractObjective",
]


@dataclass
class ObjectiveInfo:
    """Descriptor for a registered objective component."""

    name: str
    description: str
    weight: int = 1
    math_reference: str = ""
    is_enabled: bool = True


class AbstractObjective(ABC):
    """Base class every objective plug-in must implement."""

    @property
    @abstractmethod
    def info(self) -> ObjectiveInfo: ...

    @abstractmethod
    def compute_terms(self, context: OptimizationContext) -> list[tuple[Any, int]]:
        """Return (variable, coefficient) pairs for this objective."""
        ...

    @abstractmethod
    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        """Check required data. Returns error messages (empty = OK)."""
        ...

    @property
    def name(self) -> str:
        return self.info.name

    @property
    def is_enabled(self) -> bool:
        return self.info.is_enabled

    def enable(self) -> None:
        self.info.is_enabled = True

    def disable(self) -> None:
        self.info.is_enabled = False
