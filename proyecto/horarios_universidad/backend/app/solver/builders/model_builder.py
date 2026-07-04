"""CP-SAT model builder — 8-stage pipeline (Doc 09)."""

from __future__ import annotations

from ortools.sat.python import cp_model

from app.core.logging.logger import get_logger
from app.solver.builders.base import AbstractModelBuilder
from app.solver.context import OptimizationContext, OptimizationProblem
from app.solver.preprocessing import build_indices, filter_domains
from app.solver.validator.pipeline import SolverValidationPipeline
from app.solver.variables.factory import VariableFactory

__all__ = ["CpSatModelBuilder"]

_logger = get_logger(__name__)


class CpSatModelBuilder(AbstractModelBuilder):
    """Translates an OptimizationProblem into a fully-variabled CP-SAT context."""

    def __init__(self, validation_pipeline: SolverValidationPipeline | None = None) -> None:
        self._pipeline = validation_pipeline or SolverValidationPipeline()
        self._var_factory = VariableFactory()

    def build(self, problem: OptimizationProblem) -> OptimizationContext:
        """Execute the 8-stage model-building pipeline and return the context."""
        _logger.info(
            "Building CP-SAT model: %d groups, %d instructors, %d classrooms",
            len(problem.groups),
            len(problem.instructors),
            len(problem.classrooms),
        )

        # Stage 1 — create solver model
        model = cp_model.CpModel()

        # Stage 2 — build index structures
        index = build_indices(problem)
        _logger.debug("Index built: %d groups, %d slots", len(index.groups_by_id), len(index.all_slots))

        # Stage 3 — domain filtering (HD-07/08/17/18)
        index = filter_domains(problem, index)

        # Stage 4 — validation
        validation = self._pipeline.validate(problem)
        if not validation.is_valid:
            _logger.error("Validation failed: %s", validation.errors)
            raise ValueError(f"Problem validation failed: {validation.errors}")
        for warning in validation.warnings:
            _logger.warning("Validation warning: %s", warning)

        # Stage 5 — build context
        context = OptimizationContext(problem=problem, model=model)

        # Stage 6 — store index in metadata
        context._metadata["index"] = index

        # Stage 7 — create variables
        self._var_factory.create_all(model, problem, index, context)

        _logger.info(
            "Model built: %d variable groups registered",
            len(context.variables),
        )

        # Stage 8 — return ready context (constraints applied separately by PluginManager)
        return context
