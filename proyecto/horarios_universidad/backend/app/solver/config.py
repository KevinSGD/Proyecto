"""Solver configuration and status types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "SolverStatus",
    "SolverConfiguration",
]


class SolverStatus(Enum):
    """Possible states of a solver run."""

    PENDING = "pending"
    RUNNING = "running"
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class SolverConfiguration:
    """Parameters that control solver behaviour."""

    max_time_seconds: int = 300
    num_workers: int = 4
    random_seed: int | None = None
    gap_tolerance: float = 0.0
    scale_factor: int = 1000
    log_search_progress: bool = False
    enabled_constraints: list[str] = field(default_factory=list)
    disabled_constraints: list[str] = field(default_factory=list)
    objective_weights: dict[str, int] = field(default_factory=dict)

    def is_constraint_enabled(self, name: str) -> bool:
        """Return whether a constraint should be active."""
        if self.disabled_constraints and name in self.disabled_constraints:
            return False
        if self.enabled_constraints and name not in self.enabled_constraints:
            return False
        return True

    def get_weight(self, name: str, default: int = 1) -> int:
        """Return the objective weight for *name*, falling back to *default*."""
        return self.objective_weights.get(name, default)
