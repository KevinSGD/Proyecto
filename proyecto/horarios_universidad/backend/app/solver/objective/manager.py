"""Objective registry and manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.logging.logger import get_logger
from app.solver.config import SolverConfiguration
from app.solver.objective.base import AbstractObjective, ObjectiveInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["ObjectiveManager"]

_logger = get_logger(__name__)


class ObjectiveManager:
    """Registry that holds, configures, and builds the composite objective."""

    def __init__(self) -> None:
        self._objectives: list[AbstractObjective] = []

    def register(self, objective: AbstractObjective) -> None:
        """Add an objective component to the registry."""
        self._objectives.append(objective)
        _logger.info("Registered objective '%s'", objective.name)

    def unregister(self, name: str) -> bool:
        """Remove an objective by name. Returns True if found."""
        before = len(self._objectives)
        self._objectives = [o for o in self._objectives if o.name != name]
        removed = len(self._objectives) < before
        if removed:
            _logger.info("Unregistered objective '%s'", name)
        return removed

    def enable(self, name: str) -> None:
        """Enable an objective by name."""
        for o in self._objectives:
            if o.name == name:
                o.enable()
                return

    def disable(self, name: str) -> None:
        """Disable an objective by name."""
        for o in self._objectives:
            if o.name == name:
                o.disable()
                return

    def get(self, name: str) -> AbstractObjective | None:
        """Look up an objective by name."""
        for o in self._objectives:
            if o.name == name:
                return o
        return None

    def list_all(self) -> list[ObjectiveInfo]:
        """Return descriptors for every registered objective."""
        return [o.info for o in self._objectives]

    def list_enabled(self) -> list[AbstractObjective]:
        """Return only the currently-enabled objectives."""
        return [o for o in self._objectives if o.is_enabled]

    def build_objective(
        self, context: OptimizationContext
    ) -> list[tuple[Any, int]]:
        """Collect weighted terms from all enabled objectives."""
        all_terms: list[tuple[Any, int]] = []
        for objective in self.list_enabled():
            weight = objective.info.weight
            for var, coeff in objective.compute_terms(context):
                all_terms.append((var, coeff * weight))
            _logger.debug(
                "Objective '%s' contributed terms (weight=%d)",
                objective.name,
                weight,
            )
        return all_terms

    def configure_from(self, config: SolverConfiguration) -> None:
        """Apply weights and enable/disable flags from *config*."""
        for objective in self._objectives:
            if config.is_constraint_enabled(objective.name):
                objective.enable()
            else:
                objective.disable()
            objective.info.weight = config.get_weight(
                objective.name, objective.info.weight
            )

    @classmethod
    def from_discovery(cls) -> ObjectiveManager:
        """Create a manager with all auto-discovered objectives."""
        from app.solver.constraints.registry import discover_objectives

        manager = cls()
        for objective in discover_objectives():
            manager.register(objective)
        return manager
