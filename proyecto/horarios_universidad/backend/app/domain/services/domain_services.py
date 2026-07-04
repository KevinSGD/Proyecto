"""Pure domain services with no external dependencies."""

from __future__ import annotations

from uuid import UUID

from app.domain.value_objects.temporal import SessionPattern

__all__ = [
    "ConflictDetector",
    "SessionPatternResolver",
    "CapacityChecker",
]

# Type alias for assignment tuples used in conflict detection.
AssignmentTuple = tuple[UUID, UUID, int, int, int]
# (group_id, instructor_id, day, period, duration)


class ConflictDetector:
    """Detects time-slot conflicts among a set of assignments."""

    def detect_time_conflicts(
        self, assignments: list[AssignmentTuple],
    ) -> list[tuple[AssignmentTuple, AssignmentTuple]]:
        """Return pairs of assignments that overlap in time.

        Two assignments conflict when they share the same day and
        their period ranges overlap for either the same instructor
        or the same group.
        """
        conflicts: list[tuple[AssignmentTuple, AssignmentTuple]] = []
        count = len(assignments)
        for i in range(count):
            a = assignments[i]
            a_group, a_instr, a_day, a_start, a_dur = a
            a_end = a_start + a_dur
            for j in range(i + 1, count):
                b = assignments[j]
                b_group, b_instr, b_day, b_start, b_dur = b
                if a_day != b_day:
                    continue
                b_end = b_start + b_dur
                periods_overlap = a_start < b_end and b_start < a_end
                if not periods_overlap:
                    continue
                shares_resource = (
                    a_group == b_group or a_instr == b_instr
                )
                if shares_resource:
                    conflicts.append((a, b))
        return conflicts


class SessionPatternResolver:
    """Resolves which session pattern fits a given credit-hour count."""

    def resolve(
        self,
        credit_hours: int,
        patterns: list[SessionPattern],
    ) -> SessionPattern | None:
        """Return the first pattern matching *credit_hours*, or None."""
        for pattern in patterns:
            if pattern.credit_hours == credit_hours:
                return pattern
        return None

    def validate_pattern(self, pattern: SessionPattern) -> bool:
        """Check that block durations sum to at least the credit hours."""
        total = sum(pattern.block_durations)
        return (
            total >= pattern.credit_hours
            and len(pattern.block_durations) == pattern.num_blocks
        )


class CapacityChecker:
    """Checks classroom capacity against enrollment numbers."""

    def check(self, enrollment: int, capacity: int) -> bool:
        """Return True when the classroom can hold the enrollment."""
        return enrollment <= capacity

    def find_compatible_classrooms(
        self,
        enrollment: int,
        classrooms: list[tuple[UUID, int]],
    ) -> list[UUID]:
        """Return IDs of classrooms with sufficient capacity."""
        return [
            room_id
            for room_id, cap in classrooms
            if cap >= enrollment
        ]
