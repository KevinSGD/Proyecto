"""Optimization result types returned by the solver."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId
from app.solver.config import SolverConfiguration, SolverStatus

__all__ = [
    "SolverStatistics",
    "SessionResult",
    "AssignmentResult",
    "OptimizationResult",
]


@dataclass
class SolverStatistics:
    """Metrics collected during an optimization run."""

    # Problem size
    groups_total: int = 0
    groups_scheduled: int = 0
    instructors_total: int = 0
    rooms_total: int = 0
    time_slots_total: int = 0

    # Model size
    num_variables: int = 0
    num_constraints: int = 0
    variables_by_category: dict[str, int] = field(default_factory=dict)
    constraints_by_type: dict[str, int] = field(default_factory=dict)
    hard_constraints_total: int = 0
    soft_constraints_total: int = 0

    # Timing
    elapsed_seconds: float = 0.0
    timings: dict[str, float] = field(default_factory=dict)

    # Memory
    memory_usage_mb: float | None = None

    # Solution quality
    objective_value: float | None = None
    gap: float | None = None
    workload_spread: float | None = None
    avg_preference_score: float | None = None
    room_utilization_pct: float | None = None


@dataclass
class SessionResult:
    """A single scheduled session block."""

    block_index: int
    day_of_week: int
    start_period: int
    duration: int
    classroom_id: EntityId


@dataclass
class AssignmentResult:
    """Complete assignment for one group."""

    group_id: EntityId
    instructor_id: EntityId
    sessions: list[SessionResult] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Top-level outcome of a solver run."""

    status: SolverStatus
    assignments: list[AssignmentResult] = field(default_factory=list)
    statistics: SolverStatistics | None = None
    solver_config: SolverConfiguration | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def is_feasible(self) -> bool:
        """True when the solver found at least one valid solution."""
        return self.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)

    @property
    def is_optimal(self) -> bool:
        """True when the solver proved optimality."""
        return self.status is SolverStatus.OPTIMAL

    @classmethod
    def infeasible(cls, errors: list[str]) -> OptimizationResult:
        """Convenience factory for an infeasible outcome."""
        return cls(status=SolverStatus.INFEASIBLE, errors=errors)

    @classmethod
    def timeout(
        cls,
        stats: SolverStatistics,
        assignments: list[AssignmentResult],
        config: SolverConfiguration,
    ) -> OptimizationResult:
        """Convenience factory for a timeout outcome."""
        return cls(
            status=SolverStatus.TIMEOUT,
            assignments=assignments,
            statistics=stats,
            solver_config=config,
        )
