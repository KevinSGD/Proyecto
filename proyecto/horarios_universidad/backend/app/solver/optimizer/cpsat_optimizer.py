"""CP-SAT solve driver — Doc 09 Module 7."""

from __future__ import annotations

import time

from ortools.sat.python import cp_model

from app.core.logging.logger import get_logger
from app.solver.config import SolverConfiguration, SolverStatus
from app.solver.context import OptimizationContext
from app.solver.optimizer.base import AbstractOptimizer
from app.solver.result import OptimizationResult, SolverStatistics
from app.solver.statistics.collector import StatisticsCollector

__all__ = ["CpSatOptimizer"]

_logger = get_logger(__name__)

_CPSAT_STATUS_MAP: dict[int, SolverStatus] = {
    cp_model.OPTIMAL: SolverStatus.OPTIMAL,
    cp_model.FEASIBLE: SolverStatus.FEASIBLE,
    cp_model.INFEASIBLE: SolverStatus.INFEASIBLE,
    cp_model.UNKNOWN: SolverStatus.TIMEOUT,
    cp_model.MODEL_INVALID: SolverStatus.ERROR,
}


class CpSatOptimizer(AbstractOptimizer):
    """Wraps cp_model.CpSolver with project configuration."""

    def __init__(self) -> None:
        self._config: SolverConfiguration = SolverConfiguration()

    def configure(self, config: SolverConfiguration) -> None:
        """Store solver configuration for use in the next optimize() call."""
        self._config = config

    def optimize(self, context: OptimizationContext) -> OptimizationResult:
        """Solve the model inside *context* and return the structured result."""
        model: cp_model.CpModel = context.model
        if model is None:
            return OptimizationResult(
                status=SolverStatus.ERROR,
                errors=["No CP-SAT model found in context"],
            )

        self._apply_objective(model, context)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self._config.max_time_seconds)
        solver.parameters.num_search_workers = self._config.num_workers
        if self._config.random_seed is not None:
            solver.parameters.random_seed = self._config.random_seed
        solver.parameters.relative_gap_limit = self._config.gap_tolerance
        solver.parameters.log_search_progress = self._config.log_search_progress

        _logger.info(
            "Starting CP-SAT solve (max=%ds, workers=%d)",
            self._config.max_time_seconds,
            self._config.num_workers,
        )
        t0 = time.monotonic()
        raw_status = solver.Solve(model)
        elapsed = time.monotonic() - t0

        status = _CPSAT_STATUS_MAP.get(raw_status, SolverStatus.ERROR)
        _logger.info("CP-SAT finished: status=%s in %.2fs", status.value, elapsed)

        stats = StatisticsCollector.from_problem(context.problem)
        stats.num_constraints = context.constraint_count
        stats.elapsed_seconds = elapsed

        if status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            stats.objective_value = solver.ObjectiveValue()
            stats.gap = solver.BestObjectiveBound() - solver.ObjectiveValue()
            # Store solver + status so SolutionExtractor.extract(context) can read them
            context._metadata["solver"] = solver
            context._metadata["solve_status"] = status
            assignments = self._extract_assignments(solver, context)
            stats.groups_scheduled = len(assignments)
            result = OptimizationResult(
                status=status,
                assignments=assignments,
                statistics=stats,
                solver_config=self._config,
            )
        else:
            result = OptimizationResult(
                status=status,
                statistics=stats,
                solver_config=self._config,
                errors=[f"Solver returned status: {status.value}"],
            )

        return result

    def _apply_objective(
        self, model: cp_model.CpModel, context: OptimizationContext
    ) -> None:
        """Read objective terms stored in context metadata and apply to model."""
        terms: list[tuple] = context._metadata.get("objective_terms", [])
        if not terms:
            _logger.warning("No objective terms found in context — solving feasibility only")
            return
        model.Maximize(sum(var * coeff for var, coeff in terms))

    def _extract_assignments(
        self, solver: cp_model.CpSolver, context: OptimizationContext
    ) -> list:
        """Use the extractor from context metadata, or fall back to SolutionExtractor."""
        from app.solver.extractor.solution_extractor import SolutionExtractor

        extractor = context._metadata.get("extractor")
        if extractor is None:
            extractor = SolutionExtractor()

        result = extractor.extract(context)
        return result.assignments if hasattr(result, "assignments") else result
