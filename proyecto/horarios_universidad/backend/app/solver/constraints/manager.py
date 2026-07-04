"""Constraint registry and manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging.logger import get_logger
from app.solver.config import SolverConfiguration
from app.solver.constraints.base import AbstractConstraint, ConstraintInfo

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["ConstraintManager"]

_logger = get_logger(__name__)


class ConstraintManager:
    """Registry that holds, configures, and applies solver constraints."""

    def __init__(self) -> None:
        self._constraints: list[AbstractConstraint] = []

    def register(self, constraint: AbstractConstraint) -> None:
        """Add a constraint to the registry."""
        self._constraints.append(constraint)
        _logger.info("Registered constraint '%s'", constraint.name)

    def unregister(self, name: str) -> bool:
        """Remove a constraint by name. Returns True if found."""
        before = len(self._constraints)
        self._constraints = [c for c in self._constraints if c.name != name]
        removed = len(self._constraints) < before
        if removed:
            _logger.info("Unregistered constraint '%s'", name)
        return removed

    def enable(self, name: str) -> None:
        """Enable a constraint by name."""
        for c in self._constraints:
            if c.name == name:
                c.enable()
                return

    def disable(self, name: str) -> None:
        """Disable a constraint by name."""
        for c in self._constraints:
            if c.name == name:
                c.disable()
                return

    def get(self, name: str) -> AbstractConstraint | None:
        """Look up a constraint by name."""
        for c in self._constraints:
            if c.name == name:
                return c
        return None

    def list_all(self) -> list[ConstraintInfo]:
        """Return descriptors for every registered constraint."""
        return [c.info for c in self._constraints]

    def list_enabled(self) -> list[AbstractConstraint]:
        """Return only the currently-enabled constraints."""
        return [c for c in self._constraints if c.is_enabled]

    def apply_all(self, context: OptimizationContext) -> dict[str, int]:
        """Apply all enabled constraints and return {name: count} added."""
        results: dict[str, int] = {}
        for constraint in self.list_enabled():
            count = constraint.apply(context)
            context.increment_constraints(count)
            results[constraint.name] = count
            _logger.debug(
                "Applied constraint '%s': %d constraints", constraint.name, count
            )
        return results

    def validate_all(self, context: OptimizationContext) -> list[str]:
        """Run precondition checks on all enabled constraints."""
        errors: list[str] = []
        for constraint in self.list_enabled():
            errors.extend(constraint.validate_preconditions(context))
        return errors

    def configure_from(self, config: SolverConfiguration) -> None:
        """Enable / disable constraints according to *config*."""
        for constraint in self._constraints:
            if config.is_constraint_enabled(constraint.name):
                constraint.enable()
            else:
                constraint.disable()

    @classmethod
    def from_discovery(cls) -> ConstraintManager:
        """Create a manager with all auto-discovered constraints."""
        from app.solver.constraints.registry import discover_constraints

        manager = cls()
        for constraint in discover_constraints():
            manager.register(constraint)
        return manager
