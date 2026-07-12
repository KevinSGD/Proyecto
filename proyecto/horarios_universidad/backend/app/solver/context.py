"""Optimization context — the data container that flows through the solver pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.core.utils.types import EntityId
from app.solver.config import SolverConfiguration

if TYPE_CHECKING:
    from app.solver.preprocessing.index_builder import IndexData

__all__ = [
    "SolverGroup",
    "SolverInstructor",
    "SolverClassroom",
    "SolverTimeConfig",
    "OptimizationProblem",
    "OptimizationContext",
]


@dataclass
class SolverGroup:
    """Flattened group representation for the solver."""

    id: EntityId
    subject_id: EntityId
    group_number: int
    expected_enrollment: int
    modality: str
    schedule_type_id: EntityId
    num_blocks: int
    block_durations: tuple[int, ...]
    candidate_instructors: list[EntityId] = field(default_factory=list)
    compatible_classrooms: list[EntityId] = field(default_factory=list)
    preferred_classrooms: list[EntityId] = field(default_factory=list)
    priority: int = 2


@dataclass
class SolverInstructor:
    """Flattened instructor representation for the solver."""

    id: EntityId
    max_daily_periods: int
    max_weekly_periods: int
    min_weekly_periods: int = 0
    max_days: int | None = None
    available_slots: set[tuple[int, int]] = field(default_factory=set)
    preferences: dict[EntityId, int] = field(default_factory=dict)


@dataclass
class SolverClassroom:
    """Flattened classroom representation for the solver."""

    id: EntityId
    capacity: int
    resource_ids: set[EntityId] = field(default_factory=set)
    available_slots: set[tuple[int, int]] = field(default_factory=set)
    is_virtual: bool = False


@dataclass
class SolverTimeConfig:
    """Time-grid parameters for the solver."""

    days: list[int] = field(default_factory=list)
    periods_per_day: int = 11
    slot_duration_minutes: int = 60


@dataclass
class OptimizationProblem:
    """All input data needed to build and solve the scheduling model."""

    institution_id: EntityId
    period_id: EntityId
    groups: list[SolverGroup] = field(default_factory=list)
    instructors: list[SolverInstructor] = field(default_factory=list)
    classrooms: list[SolverClassroom] = field(default_factory=list)
    time_config: SolverTimeConfig | None = None
    config: SolverConfiguration = field(default_factory=SolverConfiguration)

    @property
    def total_slots(self) -> int:
        """Total number of (day, period) slots in the time grid."""
        if self.time_config is None:
            return 0
        return len(self.time_config.days) * self.time_config.periods_per_day


@dataclass
class OptimizationContext:
    """Mutable state passed through the solver pipeline stages."""

    problem: OptimizationProblem
    model: Any = None
    variables: dict[str, Any] = field(default_factory=dict)
    constraint_count: int = 0
    _metadata: dict[str, Any] = field(default_factory=dict)

    def add_variable_group(self, name: str, variables: Any) -> None:
        """Register a named collection of solver variables."""
        self.variables[name] = variables

    def get_variable_group(self, name: str) -> Any:
        """Retrieve a previously-registered variable collection."""
        return self.variables.get(name)

    def increment_constraints(self, count: int = 1) -> None:
        """Track how many constraints have been added."""
        self.constraint_count += count

    @property
    def index(self) -> IndexData | None:
        """Return the precomputed IndexData stored during model building."""
        return self._metadata.get("index")
