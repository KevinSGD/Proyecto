"""Plugin system — unified facade over constraints and objectives."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.solver.config import SolverConfiguration
from app.solver.constraints.base import AbstractConstraint, ConstraintInfo
from app.solver.constraints.manager import ConstraintManager
from app.solver.objective.base import AbstractObjective, ObjectiveInfo
from app.solver.objective.manager import ObjectiveManager

if TYPE_CHECKING:
    from app.solver.context import OptimizationContext

__all__ = ["PluginManager"]


class PluginManager:
    """Single entry-point for registering and running solver plug-ins."""

    def __init__(self) -> None:
        self.constraint_manager = ConstraintManager()
        self.objective_manager = ObjectiveManager()

    def register_constraint(self, constraint: AbstractConstraint) -> None:
        """Register a constraint plug-in."""
        self.constraint_manager.register(constraint)

    def register_objective(self, objective: AbstractObjective) -> None:
        """Register an objective plug-in."""
        self.objective_manager.register(objective)

    def configure(self, config: SolverConfiguration) -> None:
        """Propagate configuration to both managers."""
        self.constraint_manager.configure_from(config)
        self.objective_manager.configure_from(config)

    def apply_constraints(self, context: OptimizationContext) -> dict[str, int]:
        """Apply all enabled constraints and return counts."""
        return self.constraint_manager.apply_all(context)

    def build_objective(
        self, context: OptimizationContext
    ) -> list[tuple[Any, int]]:
        """Collect weighted terms from all enabled objectives."""
        return self.objective_manager.build_objective(context)

    def validate_all(self, context: OptimizationContext) -> list[str]:
        """Run precondition checks across constraints and objectives."""
        errors = self.constraint_manager.validate_all(context)
        for obj in self.objective_manager.list_enabled():
            errors.extend(obj.validate_preconditions(context))
        return errors

    def get_constraint_info(self) -> list[ConstraintInfo]:
        """Return descriptors for every registered constraint."""
        return self.constraint_manager.list_all()

    def get_objective_info(self) -> list[ObjectiveInfo]:
        """Return descriptors for every registered objective."""
        return self.objective_manager.list_all()

    @classmethod
    def from_discovery(cls) -> PluginManager:
        """Create a plugin manager with all auto-discovered constraints and objectives."""
        manager = cls()
        manager.constraint_manager = ConstraintManager.from_discovery()
        manager.objective_manager = ObjectiveManager.from_discovery()
        return manager
