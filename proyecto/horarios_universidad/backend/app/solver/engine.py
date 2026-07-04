"""SolverEngine — top-level orchestrator for the 8-stage pipeline (Doc 09).

Wires together: validation → index building → domain filtering →
variable creation → constraint application → objective building →
CP-SAT solve → solution extraction.

Usage:
    engine = SolverEngine()
    result = engine.solve(problem)
"""

from __future__ import annotations

import time
import tracemalloc

from app.core.logging.logger import get_logger
from app.solver.builders.model_builder import CpSatModelBuilder
from app.solver.config import SolverConfiguration
from app.solver.context import OptimizationContext, OptimizationProblem
from app.solver.optimizer.cpsat_optimizer import CpSatOptimizer
from app.solver.plugin import PluginManager
from app.solver.result import OptimizationResult, SolverStatistics
from app.solver.statistics.collector import StatisticsCollector

__all__ = ["SolverEngine"]

_logger = get_logger(__name__)


class SolverEngine:
    """End-to-end solver orchestrator — the only public entry point."""

    def __init__(
        self,
        config: SolverConfiguration | None = None,
        plugin_manager: PluginManager | None = None,
    ) -> None:
        self._config = config or SolverConfiguration()
        self._plugins = plugin_manager or PluginManager.from_discovery()
        self._builder = CpSatModelBuilder()
        self._optimizer = CpSatOptimizer()

    def solve(self, problem: OptimizationProblem) -> OptimizationResult:
        """Execute the full pipeline and return the optimisation result."""
        tracemalloc.start()
        timings: dict[str, float] = {}
        t_total = time.monotonic()

        _logger.info(
            "SolverEngine.solve — %d groups, %d instructors, %d classrooms",
            len(problem.groups),
            len(problem.instructors),
            len(problem.classrooms),
        )

        # Stage 1-7: Build model (index, domain filter, validate, variables)
        t0 = time.monotonic()
        try:
            context = self._builder.build(problem)
        except ValueError as exc:
            _logger.error("Model building failed: %s", exc)
            return OptimizationResult.infeasible([str(exc)])
        timings["model_build"] = time.monotonic() - t0

        # Configure plugins from solver config
        self._plugins.configure(self._config)

        # Precondition validation
        t0 = time.monotonic()
        precondition_errors = self._plugins.validate_all(context)
        timings["precondition_check"] = time.monotonic() - t0
        if precondition_errors:
            for err in precondition_errors:
                _logger.warning("Precondition error: %s", err)

        # Apply constraints
        t0 = time.monotonic()
        constraint_counts = self._plugins.apply_constraints(context)
        timings["constraints"] = time.monotonic() - t0
        _logger.info(
            "Constraints applied: %d types, %d total",
            len(constraint_counts),
            sum(constraint_counts.values()),
        )

        # Build objective
        t0 = time.monotonic()
        objective_terms = self._plugins.build_objective(context)
        context._metadata["objective_terms"] = objective_terms
        timings["objective"] = time.monotonic() - t0
        _logger.info("Objective built: %d terms", len(objective_terms))

        # Solve
        self._optimizer.configure(self._config)
        t0 = time.monotonic()
        result = self._optimizer.optimize(context)
        timings["solve"] = time.monotonic() - t0

        timings["total"] = time.monotonic() - t_total

        # Memory snapshot
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb = peak_bytes / (1024 * 1024)

        # Enrich statistics
        result.statistics = self._build_statistics(
            problem, context, constraint_counts, timings, result, peak_mb,
        )

        _logger.info(
            "SolverEngine complete — status=%s, objective=%s, time=%.2fs",
            result.status.value,
            result.statistics.objective_value,
            timings["total"],
        )

        return result

    def _build_statistics(
        self,
        problem: OptimizationProblem,
        context: OptimizationContext,
        constraint_counts: dict[str, int],
        timings: dict[str, float],
        result: OptimizationResult,
        peak_mb: float,
    ) -> SolverStatistics:
        """Assemble comprehensive statistics from the pipeline run."""
        stats = result.statistics or StatisticsCollector.from_problem(problem)

        # Variable counts by category
        variables_by_category: dict[str, int] = {}
        for name, group in context.variables.items():
            if isinstance(group, dict):
                variables_by_category[name] = len(group)
            else:
                variables_by_category[name] = 1
        stats.num_variables = sum(variables_by_category.values())
        stats.variables_by_category = variables_by_category

        # Constraint counts by name
        hard_count = sum(
            v for k, v in constraint_counts.items() if k.startswith("HD")
        )
        soft_count = sum(
            v for k, v in constraint_counts.items() if k.startswith("SB")
        )
        stats.constraints_by_type = constraint_counts
        stats.hard_constraints_total = hard_count
        stats.soft_constraints_total = soft_count
        stats.num_constraints = context.constraint_count

        # Timings and memory
        stats.timings = timings
        stats.memory_usage_mb = round(peak_mb, 2)

        # Problem metadata
        stats.groups_total = len(problem.groups)
        stats.instructors_total = len(problem.instructors)
        stats.rooms_total = len(problem.classrooms)
        stats.time_slots_total = problem.total_slots

        # Post-solve quality metrics
        if result.is_feasible:
            StatisticsCollector.compute_quality_metrics(result, problem)

        return stats
