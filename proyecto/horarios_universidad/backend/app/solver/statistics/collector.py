"""Statistics collection helpers."""

from __future__ import annotations

from app.solver.context import OptimizationProblem
from app.solver.result import OptimizationResult, SolverStatistics

__all__ = ["StatisticsCollector"]


class StatisticsCollector:
    """Builds and updates SolverStatistics at each pipeline stage."""

    @staticmethod
    def from_problem(problem: OptimizationProblem) -> SolverStatistics:
        """Create initial stats from the input data."""
        return SolverStatistics(
            groups_total=len(problem.groups),
            instructors_total=len(problem.instructors),
            rooms_total=len(problem.classrooms),
            time_slots_total=problem.total_slots,
        )

    @staticmethod
    def update_model_stats(
        stats: SolverStatistics,
        num_variables: int,
        num_constraints: int,
        constraints_by_type: dict[str, int],
    ) -> SolverStatistics:
        """Enrich stats with model-building metrics."""
        stats.num_variables = num_variables
        stats.num_constraints = num_constraints
        stats.constraints_by_type = constraints_by_type
        return stats

    @staticmethod
    def update_solution_stats(
        stats: SolverStatistics,
        elapsed: float,
        objective: float | None,
        gap: float | None,
        groups_scheduled: int,
    ) -> SolverStatistics:
        """Enrich stats with post-solve metrics."""
        stats.elapsed_seconds = elapsed
        stats.objective_value = objective
        stats.gap = gap
        stats.groups_scheduled = groups_scheduled
        return stats

    @staticmethod
    def compute_quality_metrics(
        result: OptimizationResult,
        problem: OptimizationProblem,
    ) -> SolverStatistics:
        """Compute quality metrics from the final result."""
        stats = result.statistics or SolverStatistics()

        # Workload spread: std-dev of periods assigned per instructor
        periods_by_instructor: dict[object, int] = {}
        for assignment in result.assignments:
            total = sum(s.duration for s in assignment.sessions)
            periods_by_instructor[assignment.instructor_id] = (
                periods_by_instructor.get(assignment.instructor_id, 0) + total
            )
        if periods_by_instructor:
            values = list(periods_by_instructor.values())
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            stats.workload_spread = variance**0.5

        # Average preference score
        instructor_map = {i.id: i for i in problem.instructors}
        pref_scores: list[int] = []
        for assignment in result.assignments:
            inst = instructor_map.get(assignment.instructor_id)
            if inst and assignment.group_id in inst.preferences:
                pref_scores.append(inst.preferences[assignment.group_id])
        if pref_scores:
            stats.avg_preference_score = sum(pref_scores) / len(pref_scores)

        # Room utilization
        total_capacity_used = 0
        total_capacity_available = 0
        classroom_map = {c.id: c for c in problem.classrooms}
        for assignment in result.assignments:
            for session in assignment.sessions:
                room = classroom_map.get(session.classroom_id)
                if room:
                    total_capacity_used += 1
                    total_capacity_available += 1
        if total_capacity_available > 0:
            slots_total = problem.total_slots * len(problem.classrooms)
            if slots_total > 0:
                stats.room_utilization_pct = (
                    total_capacity_used / slots_total
                ) * 100.0

        return stats
