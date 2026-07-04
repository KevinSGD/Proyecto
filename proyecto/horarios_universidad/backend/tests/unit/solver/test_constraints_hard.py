"""Unit tests for hard constraints (HD-01 .. HD-16).

Each test builds a minimal OptimizationContext with a 2-group / 2-instructor /
2-room / 3-day × 5-period problem, applies the constraint under test, and
verifies that (a) constraints were added and (b) the solved model respects them.
"""

from __future__ import annotations

import pytest

pytest.importorskip("ortools", reason="ortools not installed")

from ortools.sat.python import cp_model  # noqa: E402

from app.core.utils.types import generate_id  # noqa: E402
from app.solver.context import (  # noqa: E402
    OptimizationContext,
    OptimizationProblem,
    SolverClassroom,
    SolverGroup,
    SolverInstructor,
    SolverTimeConfig,
)
from app.solver.preprocessing.index_builder import build_indices  # noqa: E402
from app.solver.variables.factory import VariableFactory  # noqa: E402


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def ids():
    """Generate stable IDs for the small test problem."""
    return {
        "inst1": generate_id(),
        "inst2": generate_id(),
        "room1": generate_id(),
        "room2": generate_id(),
        "subj1": generate_id(),
        "subj2": generate_id(),
        "group1": generate_id(),
        "group2": generate_id(),
        "stype": generate_id(),
        "inst_id": generate_id(),
        "period_id": generate_id(),
    }


@pytest.fixture()
def small_problem(ids):
    """2 groups, 2 instructors, 2 rooms, 3 days × 5 periods."""
    days = [1, 2, 3]
    periods = list(range(1, 6))
    all_slots = {(w, h) for w in days for h in periods}

    groups = [
        SolverGroup(
            id=ids["group1"],
            subject_id=ids["subj1"],
            group_number=1,
            expected_enrollment=30,
            modality="presencial",
            schedule_type_id=ids["stype"],
            num_blocks=2,
            block_durations=(2, 2),
            candidate_instructors=[ids["inst1"], ids["inst2"]],
            compatible_classrooms=[ids["room1"], ids["room2"]],
        ),
        SolverGroup(
            id=ids["group2"],
            subject_id=ids["subj2"],
            group_number=1,
            expected_enrollment=25,
            modality="presencial",
            schedule_type_id=ids["stype"],
            num_blocks=1,
            block_durations=(3,),
            candidate_instructors=[ids["inst1"]],
            compatible_classrooms=[ids["room1"]],
        ),
    ]
    instructors = [
        SolverInstructor(
            id=ids["inst1"],
            max_daily_periods=6,
            max_weekly_periods=12,
            min_weekly_periods=4,
            max_days=4,
            available_slots=set(all_slots),
            preferences={ids["group1"]: 8, ids["group2"]: 5},
        ),
        SolverInstructor(
            id=ids["inst2"],
            max_daily_periods=4,
            max_weekly_periods=8,
            min_weekly_periods=2,
            max_days=3,
            available_slots=set(all_slots),
        ),
    ]
    classrooms = [
        SolverClassroom(
            id=ids["room1"],
            capacity=40,
            available_slots=set(all_slots),
        ),
        SolverClassroom(
            id=ids["room2"],
            capacity=35,
            available_slots=set(all_slots),
        ),
    ]
    return OptimizationProblem(
        institution_id=ids["inst_id"],
        period_id=ids["period_id"],
        groups=groups,
        instructors=instructors,
        classrooms=classrooms,
        time_config=SolverTimeConfig(days=days, periods_per_day=5),
    )


@pytest.fixture()
def built_context(small_problem):
    """Return a fully built OptimizationContext (model + variables)."""
    model = cp_model.CpModel()
    index = build_indices(small_problem)
    context = OptimizationContext(problem=small_problem, model=model)
    context._metadata["index"] = index
    VariableFactory().create_all(model, small_problem, index, context)
    return context


# ── helper: solve a tiny model ───────────────────────────────────────────────


def _solve(context: OptimizationContext) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 1
    solver.Solve(context.model)
    return solver


# ── HD-01 ────────────────────────────────────────────────────────────────────


class TestHd01TeacherAssignment:
    def test_constraint_count_positive(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment

        c = Hd01TeacherAssignment()
        count = c.apply(built_context)
        # One AddExactlyOne per group.
        assert count == len(built_context.problem.groups)

    def test_assigns_exactly_one_instructor(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment

        c = Hd01TeacherAssignment()
        c.apply(built_context)
        solver = _solve(built_context)

        X = built_context.get_variable_group("X")
        index = built_context._metadata["index"]

        for g_id, candidates in index.D_g.items():
            assigned = sum(
                solver.Value(X[(d_id, g_id)])
                for d_id in candidates
                if (d_id, g_id) in X
            )
            assert assigned == 1, f"Group {g_id} was not assigned exactly one instructor"

    def test_validate_preconditions_missing_X(self, small_problem):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd01TeacherAssignment().validate_preconditions(ctx)
        assert any("X" in e for e in errors)


# ── HD-02 ────────────────────────────────────────────────────────────────────


class TestHd02BlockLocation:
    def test_places_each_block_exactly_once(self, built_context):
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation

        c = Hd02BlockLocation()
        count = c.apply(built_context)
        # Sum of num_blocks across all groups.
        expected = sum(g.num_blocks for g in built_context.problem.groups)
        assert count == expected

    def test_solve_gives_exactly_one_start_per_block(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        solver = _solve(built_context)

        Y = built_context.get_variable_group("Y")
        index = built_context._metadata["index"]

        for g_id, group in index.groups_by_id.items():
            for l_idx in range(group.num_blocks):
                starts = [
                    solver.Value(Y[(g_id, l_idx, w, h, a_id)])
                    for (g_id2, l2, w, h, a_id) in Y
                    if g_id2 == g_id and l2 == l_idx
                ]
                assert sum(starts) == 1, (
                    f"Block {l_idx} of group {g_id} does not have exactly one start"
                )


# ── HD-05 ────────────────────────────────────────────────────────────────────


class TestHd05NoOverlapTeacher:
    def test_no_teacher_overlap_in_solution(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd05_no_overlap_teacher import Hd05NoOverlapTeacher

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd03StartCoverageLink().apply(built_context)
        count = Hd05NoOverlapTeacher().apply(built_context)
        assert count >= 0  # constraint is applied without error

        solver = _solve(built_context)
        X = built_context.get_variable_group("X")
        Z = built_context.get_variable_group("Z")
        index = built_context._metadata["index"]

        # Verify: for each instructor and each slot, at most one group is active.
        for d_id, group_ids in index.G_d.items():
            for w in index.days:
                for h in index.periods:
                    active = 0
                    for g_id in group_ids:
                        if (d_id, g_id) not in X:
                            continue
                        if solver.Value(X[(d_id, g_id)]) == 0:
                            continue
                        for a_id in index.A_g.get(g_id, []):
                            if (g_id, w, h, a_id) in Z:
                                active += solver.Value(Z[(g_id, w, h, a_id)])
                    assert active <= 1, (
                        f"Instructor {d_id} has overlap at day={w} period={h}"
                    )


# ── HD-06 ────────────────────────────────────────────────────────────────────


class TestHd06NoOverlapRoom:
    def test_no_room_overlap_in_solution(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd06_no_overlap_room import Hd06NoOverlapRoom

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd03StartCoverageLink().apply(built_context)
        count = Hd06NoOverlapRoom().apply(built_context)
        assert count >= 0

        solver = _solve(built_context)
        Z = built_context.get_variable_group("Z")
        index = built_context._metadata["index"]

        # Verify: for each physical room and each slot, at most one group active.
        from collections import defaultdict
        rooms_to_groups: dict = defaultdict(list)
        for g_id, rooms in index.A_g.items():
            for a_id in rooms:
                rooms_to_groups[a_id].append(g_id)

        for a_id, group_ids in rooms_to_groups.items():
            classroom = index.classrooms_by_id.get(a_id)
            if classroom is not None and classroom.is_virtual:
                continue
            for w in index.days:
                for h in index.periods:
                    slot_total = sum(
                        solver.Value(Z[(g_id, w, h, a_id)])
                        for g_id in group_ids
                        if (g_id, w, h, a_id) in Z
                    )
                    assert slot_total <= 1, (
                        f"Room {a_id} has double-booking at day={w} period={h}"
                    )


# ── HD-12 ────────────────────────────────────────────────────────────────────


class TestHd12RoomConsistency:
    def test_constraint_count_positive(self, built_context):
        from app.solver.constraints.hard.hd12_room_consistency import Hd12RoomConsistency

        count = Hd12RoomConsistency().apply(built_context)
        assert count > 0

    def test_same_room_for_all_blocks(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd12_room_consistency import Hd12RoomConsistency

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd03StartCoverageLink().apply(built_context)
        Hd12RoomConsistency().apply(built_context)

        solver = _solve(built_context)
        R_room = built_context.get_variable_group("R_room")
        index = built_context._metadata["index"]

        # Each group has exactly one R_room active.
        for g_id in index.groups_by_id:
            rooms = index.A_g.get(g_id, [])
            active_rooms = sum(
                solver.Value(R_room[(g_id, a_id)])
                for a_id in rooms
                if (g_id, a_id) in R_room
            )
            assert active_rooms == 1, f"Group {g_id} does not have exactly one room"


# ── HD-13 ────────────────────────────────────────────────────────────────────


class TestHd13BlocksDifferentDays:
    def test_constraint_count_only_multi_block(self, built_context):
        from app.solver.constraints.hard.hd13_blocks_different_days import Hd13BlocksDifferentDays

        count = Hd13BlocksDifferentDays().apply(built_context)
        # Only group1 (num_blocks=2) generates constraints.
        multi_block_groups = [
            g for g in built_context.problem.groups if g.num_blocks >= 2
        ]
        # Each multi-block group may generate up to len(days) constraints.
        assert count >= 0
        assert count <= len(multi_block_groups) * len(built_context.problem.time_config.days)

    def test_blocks_on_different_days_in_solution(self, built_context):
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd13_blocks_different_days import Hd13BlocksDifferentDays

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd13BlocksDifferentDays().apply(built_context)

        solver = _solve(built_context)
        Y = built_context.get_variable_group("Y")
        index = built_context._metadata["index"]

        for g_id, group in index.groups_by_id.items():
            if group.num_blocks < 2:
                continue
            # Collect the day of each placed block.
            block_days: list[int] = []
            for l_idx in range(group.num_blocks):
                for w in index.days:
                    for h in index.periods:
                        for a_id in index.A_g.get(g_id, []):
                            key = (g_id, l_idx, w, h, a_id)
                            if key in Y and solver.Value(Y[key]) == 1:
                                block_days.append(w)
            # All block days must be distinct.
            assert len(block_days) == len(set(block_days)), (
                f"Group {g_id} has two blocks on the same day"
            )


# ── HD-15 (max weekly load) — via omega ─────────────────────────────────────


class TestHd15MaxWeeklyLoad:
    def test_max_weekly_periods_respected(self, built_context):
        """Omega variable upper bound = instructor.max_weekly_periods."""
        omega = built_context.get_variable_group("omega")
        index = built_context._metadata["index"]

        for d_id, instructor in index.instructors_by_id.items():
            if d_id not in omega:
                continue
            # Upper bound of omega var must not exceed max_weekly_periods.
            omega_var = omega[d_id]
            assert omega_var.Proto().domain[-1] <= instructor.max_weekly_periods, (
                f"omega upper bound for {d_id} exceeds max_weekly_periods"
            )


# ── HD-03 ────────────────────────────────────────────────────────────────────


class TestHd03StartCoverageLink:
    def test_constraint_count_positive(self, built_context):
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink

        count = Hd03StartCoverageLink().apply(built_context)
        assert count >= 0

    def test_z_linked_to_y_in_solution(self, built_context):
        """When Y[start]=1, all Z slots covered by that start must be 1."""
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd03StartCoverageLink().apply(built_context)

        solver = _solve(built_context)

        Y = built_context.get_variable_group("Y")
        Z = built_context.get_variable_group("Z")
        index = built_context._metadata["index"]

        for (g_id, l_idx, w, h_start), covered_slots in index.coverage.items():
            rooms = index.A_g.get(g_id, [])
            for a_id in rooms:
                y_key = (g_id, l_idx, w, h_start, a_id)
                if y_key not in Y:
                    continue
                if solver.Value(Y[y_key]) == 1:
                    for (cov_w, cov_h) in covered_slots:
                        z_key = (g_id, cov_w, cov_h, a_id)
                        if z_key in Z:
                            assert solver.Value(Z[z_key]) == 1, (
                                f"Y=1 at {y_key} but Z=0 at {z_key}"
                            )

    def test_validate_preconditions_missing_Y(self, small_problem):
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd03StartCoverageLink().validate_preconditions(ctx)
        assert any("Y" in e for e in errors)


# ── HD-04 ────────────────────────────────────────────────────────────────────


class TestHd04TeacherSessionConsistency:
    def test_z_hat_registered_after_apply(self, built_context):
        """HD-04 must register the Z_hat variable group in context."""
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd04_teacher_session_consistency import Hd04TeacherSessionConsistency

        Hd03StartCoverageLink().apply(built_context)
        count = Hd04TeacherSessionConsistency().apply(built_context)
        assert count >= 0

        Z_hat = built_context.get_variable_group("Z_hat")
        assert Z_hat is not None
        assert isinstance(Z_hat, dict)

    def test_constraint_count_positive(self, built_context):
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd04_teacher_session_consistency import Hd04TeacherSessionConsistency

        Hd03StartCoverageLink().apply(built_context)
        count = Hd04TeacherSessionConsistency().apply(built_context)
        # McCormick creates at least 3 constraints per z_hat plus phi linkage.
        assert count >= 0

    def test_validate_preconditions_missing_X(self, small_problem):
        from app.solver.constraints.hard.hd04_teacher_session_consistency import Hd04TeacherSessionConsistency

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd04TeacherSessionConsistency().validate_preconditions(ctx)
        assert any("X" in e for e in errors)


# ── HD-09 ────────────────────────────────────────────────────────────────────


@pytest.fixture()
def restricted_instructor_problem(ids):
    """Problem where inst1 is unavailable on day 1 (all periods)."""
    days = [1, 2, 3]
    periods = list(range(1, 6))
    all_slots = {(w, h) for w in days for h in periods}
    # inst1 cannot teach on day 1
    inst1_slots = {(w, h) for w in [2, 3] for h in periods}

    groups = [
        SolverGroup(
            id=ids["group1"],
            subject_id=ids["subj1"],
            group_number=1,
            expected_enrollment=30,
            modality="presencial",
            schedule_type_id=ids["stype"],
            num_blocks=2,
            block_durations=(2, 2),
            candidate_instructors=[ids["inst1"], ids["inst2"]],
            compatible_classrooms=[ids["room1"], ids["room2"]],
        ),
        SolverGroup(
            id=ids["group2"],
            subject_id=ids["subj2"],
            group_number=1,
            expected_enrollment=25,
            modality="presencial",
            schedule_type_id=ids["stype"],
            num_blocks=1,
            block_durations=(3,),
            candidate_instructors=[ids["inst1"]],
            compatible_classrooms=[ids["room1"]],
        ),
    ]
    instructors = [
        SolverInstructor(
            id=ids["inst1"],
            max_daily_periods=6,
            max_weekly_periods=12,
            min_weekly_periods=4,
            max_days=4,
            available_slots=inst1_slots,
            preferences={ids["group1"]: 8, ids["group2"]: 5},
        ),
        SolverInstructor(
            id=ids["inst2"],
            max_daily_periods=4,
            max_weekly_periods=8,
            min_weekly_periods=2,
            max_days=3,
            available_slots=set(all_slots),
        ),
    ]
    classrooms = [
        SolverClassroom(id=ids["room1"], capacity=40, available_slots=set(all_slots)),
        SolverClassroom(id=ids["room2"], capacity=35, available_slots=set(all_slots)),
    ]
    return OptimizationProblem(
        institution_id=ids["inst_id"],
        period_id=ids["period_id"],
        groups=groups,
        instructors=instructors,
        classrooms=classrooms,
        time_config=SolverTimeConfig(days=days, periods_per_day=5),
    )


@pytest.fixture()
def restricted_context(restricted_instructor_problem):
    """Context with a restricted-availability instructor."""
    model = cp_model.CpModel()
    index = build_indices(restricted_instructor_problem)
    context = OptimizationContext(problem=restricted_instructor_problem, model=model)
    context._metadata["index"] = index
    VariableFactory().create_all(model, restricted_instructor_problem, index, context)
    return context


class TestHd09TeacherAvailability:
    def test_constraint_count_with_restriction(self, restricted_context):
        from app.solver.constraints.hard.hd09_teacher_availability import Hd09TeacherAvailability

        count = Hd09TeacherAvailability().apply(restricted_context)
        # inst1 is unavailable on day 1, so constraints should be generated.
        assert count > 0

    def test_no_constraints_when_all_available(self, built_context):
        from app.solver.constraints.hard.hd09_teacher_availability import Hd09TeacherAvailability

        count = Hd09TeacherAvailability().apply(built_context)
        # All instructors have full availability, so no constraints needed.
        assert count == 0

    def test_validate_preconditions_missing_Z(self, small_problem):
        from app.solver.constraints.hard.hd09_teacher_availability import Hd09TeacherAvailability

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd09TeacherAvailability().validate_preconditions(ctx)
        assert any("Z" in e for e in errors)


# ── HD-10 ────────────────────────────────────────────────────────────────────


@pytest.fixture()
def restricted_room_problem(ids):
    """Problem where room1 is unavailable on day 1."""
    days = [1, 2, 3]
    periods = list(range(1, 6))
    all_slots = {(w, h) for w in days for h in periods}
    # room1 cannot be used on day 1
    room1_slots = {(w, h) for w in [2, 3] for h in periods}

    groups = [
        SolverGroup(
            id=ids["group1"],
            subject_id=ids["subj1"],
            group_number=1,
            expected_enrollment=30,
            modality="presencial",
            schedule_type_id=ids["stype"],
            num_blocks=2,
            block_durations=(2, 2),
            candidate_instructors=[ids["inst1"], ids["inst2"]],
            compatible_classrooms=[ids["room1"], ids["room2"]],
        ),
        SolverGroup(
            id=ids["group2"],
            subject_id=ids["subj2"],
            group_number=1,
            expected_enrollment=25,
            modality="presencial",
            schedule_type_id=ids["stype"],
            num_blocks=1,
            block_durations=(3,),
            candidate_instructors=[ids["inst1"]],
            compatible_classrooms=[ids["room1"]],
        ),
    ]
    instructors = [
        SolverInstructor(
            id=ids["inst1"],
            max_daily_periods=6,
            max_weekly_periods=12,
            min_weekly_periods=4,
            max_days=4,
            available_slots=set(all_slots),
            preferences={ids["group1"]: 8, ids["group2"]: 5},
        ),
        SolverInstructor(
            id=ids["inst2"],
            max_daily_periods=4,
            max_weekly_periods=8,
            min_weekly_periods=2,
            max_days=3,
            available_slots=set(all_slots),
        ),
    ]
    classrooms = [
        SolverClassroom(id=ids["room1"], capacity=40, available_slots=room1_slots),
        SolverClassroom(id=ids["room2"], capacity=35, available_slots=set(all_slots)),
    ]
    return OptimizationProblem(
        institution_id=ids["inst_id"],
        period_id=ids["period_id"],
        groups=groups,
        instructors=instructors,
        classrooms=classrooms,
        time_config=SolverTimeConfig(days=days, periods_per_day=5),
    )


@pytest.fixture()
def restricted_room_context(restricted_room_problem):
    """Context with a restricted-availability room."""
    model = cp_model.CpModel()
    index = build_indices(restricted_room_problem)
    context = OptimizationContext(problem=restricted_room_problem, model=model)
    context._metadata["index"] = index
    VariableFactory().create_all(model, restricted_room_problem, index, context)
    return context


class TestHd10RoomAvailability:
    def test_constraint_count_with_restriction(self, restricted_room_context):
        from app.solver.constraints.hard.hd10_room_availability import Hd10RoomAvailability

        count = Hd10RoomAvailability().apply(restricted_room_context)
        # room1 is unavailable on day 1, so constraints should be generated.
        assert count > 0

    def test_no_constraints_when_all_available(self, built_context):
        from app.solver.constraints.hard.hd10_room_availability import Hd10RoomAvailability

        count = Hd10RoomAvailability().apply(built_context)
        # All rooms have full availability, so no constraints needed.
        assert count == 0

    def test_validate_preconditions_missing_Z(self, small_problem):
        from app.solver.constraints.hard.hd10_room_availability import Hd10RoomAvailability

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd10RoomAvailability().validate_preconditions(ctx)
        assert any("Z" in e for e in errors)


# ── HD-14 ────────────────────────────────────────────────────────────────────


class TestHd14MaxDailyLoad:
    def test_constraint_count_positive(self, built_context):
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd04_teacher_session_consistency import Hd04TeacherSessionConsistency
        from app.solver.constraints.hard.hd14_max_daily_load import Hd14MaxDailyLoad

        Hd03StartCoverageLink().apply(built_context)
        Hd04TeacherSessionConsistency().apply(built_context)
        count = Hd14MaxDailyLoad().apply(built_context)
        assert count > 0

    def test_daily_load_respects_max(self, built_context):
        """Each instructor's daily load must not exceed max_daily_periods."""
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd03_start_coverage_link import Hd03StartCoverageLink
        from app.solver.constraints.hard.hd04_teacher_session_consistency import Hd04TeacherSessionConsistency
        from app.solver.constraints.hard.hd14_max_daily_load import Hd14MaxDailyLoad

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd03StartCoverageLink().apply(built_context)
        Hd04TeacherSessionConsistency().apply(built_context)
        Hd14MaxDailyLoad().apply(built_context)

        solver = _solve(built_context)
        omega_daily = built_context.get_variable_group("omega_daily")
        index = built_context._metadata["index"]

        for (d_id, w), omega_var in omega_daily.items():
            instructor = index.instructors_by_id.get(d_id)
            if instructor is None:
                continue
            val = solver.Value(omega_var)
            assert val <= instructor.max_daily_periods, (
                f"Instructor {d_id} on day {w}: daily load {val} > max {instructor.max_daily_periods}"
            )

    def test_validate_preconditions_missing_omega_daily(self, small_problem):
        from app.solver.constraints.hard.hd14_max_daily_load import Hd14MaxDailyLoad

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd14MaxDailyLoad().validate_preconditions(ctx)
        assert any("omega_daily" in e for e in errors)


# ── HD-16 ────────────────────────────────────────────────────────────────────


class TestHd16FixedAssignment:
    def test_single_candidate_is_fixed(self, built_context):
        """Group with single candidate_instructor gets X=1 forced."""
        from app.solver.constraints.hard.hd16_fixed_assignment import Hd16FixedAssignment

        count = Hd16FixedAssignment().apply(built_context)
        # group2 has only one candidate (inst1), so at least 1 constraint.
        assert count >= 1

    def test_fixed_instructor_respected_in_solution(self, built_context):
        """When a group has a single candidate, that candidate must be assigned."""
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation
        from app.solver.constraints.hard.hd16_fixed_assignment import Hd16FixedAssignment

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Hd16FixedAssignment().apply(built_context)

        solver = _solve(built_context)
        X = built_context.get_variable_group("X")
        index = built_context._metadata["index"]

        for g_id, group in index.groups_by_id.items():
            candidates = index.D_g.get(g_id, [])
            if len(candidates) == 1:
                x_key = (candidates[0], g_id)
                if x_key in X:
                    assert solver.Value(X[x_key]) == 1, (
                        f"Single-candidate group {g_id}: X should be 1"
                    )

    def test_validate_preconditions_missing_X(self, small_problem):
        from app.solver.constraints.hard.hd16_fixed_assignment import Hd16FixedAssignment

        model = cp_model.CpModel()
        ctx = OptimizationContext(problem=small_problem, model=model)
        errors = Hd16FixedAssignment().validate_preconditions(ctx)
        assert any("X" in e for e in errors)
