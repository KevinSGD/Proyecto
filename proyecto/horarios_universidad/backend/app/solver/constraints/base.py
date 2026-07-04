"""Abstract constraint base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = [
    "ConstraintInfo",
    "AbstractConstraint",
]


@dataclass
class ConstraintInfo:
    """Descriptor for a registered constraint."""

    name: str
    description: str
    constraint_type: str  # "hard" or "soft"
    math_reference: str  # e.g. "HD-05"
    module_path: str  # e.g. "constraints.no_overlap_instructor"
    is_enabled: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)


class AbstractConstraint(ABC):
    """Base class every constraint plug-in must implement."""

    @property
    @abstractmethod
    def info(self) -> ConstraintInfo: ...

    @abstractmethod
    def apply(self, context: OptimizationContext) -> int:
        """Apply constraint to the context. Returns count of constraints added."""
        ...

    @abstractmethod
    def validate_preconditions(self, context: OptimizationContext) -> list[str]:
        """Check required data. Returns error messages (empty = OK)."""
        ...

    @property
    def name(self) -> str:
        return self.info.name

    @property
    def is_hard(self) -> bool:
        return self.info.constraint_type == "hard"

    @property
    def is_enabled(self) -> bool:
        return self.info.is_enabled

    def enable(self) -> None:
        self.info.is_enabled = True

    def disable(self) -> None:
        self.info.is_enabled = False
