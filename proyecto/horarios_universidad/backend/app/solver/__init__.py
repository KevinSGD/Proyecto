"""Solver core — plugin-based scheduling optimization framework."""

from app.solver.builders.model_builder import CpSatModelBuilder
from app.solver.config import SolverConfiguration, SolverStatus
from app.solver.constraints.base import AbstractConstraint, ConstraintInfo
from app.solver.constraints.manager import ConstraintManager
from app.solver.context import OptimizationContext, OptimizationProblem
from app.solver.engine import SolverEngine
from app.solver.extractor.solution_extractor import SolutionExtractor
from app.solver.objective.base import AbstractObjective, ObjectiveInfo
from app.solver.objective.manager import ObjectiveManager
from app.solver.optimizer.cpsat_optimizer import CpSatOptimizer
from app.solver.plugin import PluginManager
from app.solver.preprocessing import IndexData, build_indices, filter_domains
from app.solver.result import OptimizationResult
from app.solver.variables.factory import VariableFactory

__all__ = [
    "SolverEngine",
    "SolverConfiguration",
    "SolverStatus",
    "OptimizationProblem",
    "OptimizationContext",
    "OptimizationResult",
    "PluginManager",
    "ConstraintManager",
    "ObjectiveManager",
    "AbstractConstraint",
    "ConstraintInfo",
    "AbstractObjective",
    "ObjectiveInfo",
    "CpSatModelBuilder",
    "CpSatOptimizer",
    "SolutionExtractor",
    "VariableFactory",
    "IndexData",
    "build_indices",
    "filter_domains",
]
