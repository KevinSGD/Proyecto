"""Unit tests for soft constraints (SB-01 .. SB-11).

Each test builds a minimal OptimizationContext with the shared small_problem
fixture and verifies that the soft constraint creates the expected penalty/reward
variable groups and (where applicable) that the solver finds a feasible solution.
"""

from __future__ import annotations

import gc
import pytest

pytest.importorskip("ortools", reason="ortools not installed")
gc.disable()

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


# ── shared fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def ids():
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
    all_slots = {(w, h) for w in days for h in range(1, 6)}

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
def built_context(small_problem):
    model = cp_model.CpModel()
    index = build_indices(small_problem)
    context = OptimizationContext(problem=small_problem, model=model)
    context._metadata["index"] = index
    VariableFactory().create_all(model, small_problem, index, context)
    return context


# ── SB-01: minimum weekly load ───────────────────────────────────────────────


class TestSb01MinWeeklyLoad:
    def test_penalty_variables_created(self, built_context):
        from app.solver.constraints.soft.sb01_min_weekly_load import Sb01MinWeeklyLoad

        count = Sb01MinWeeklyLoad().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb01")

        assert penalty is not None
        # At least one instructor has min_weekly_periods > 0.
        assert len(penalty) > 0

    def test_penalizes_underload(self, built_context):
        """When an instructor teaches nothing, their deficit should equal min load."""
        from app.solver.constraints.soft.sb01_min_weekly_load import Sb01MinWeeklyLoad
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Sb01MinWeeklyLoad().apply(built_context)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.Solve(built_context.model)

        penalty = built_context.get_variable_group("penalty_sb01")
        omega = built_context.get_variable_group("omega")
        index = built_context._metadata["index"]

        # Each penalty var must be >= max(0, min_load - omega).
        for d_id, penalty_var in penalty.items():
            instructor = index.instructors_by_id[d_id]
            omega_val = solver.Value(omega[d_id])
            penalty_val = solver.Value(penalty_var)
            min_load = instructor.min_weekly_periods
            expected_min_penalty = max(0, min_load - omega_val)
            assert penalty_val >= expected_min_penalty, (
                f"Instructor {d_id}: penalty={penalty_val} "
                f"but min_load={min_load}, omega={omega_val}"
            )

    def test_validate_preconditions(self, small_problem):
        from app.solver.constraints.soft.sb01_min_weekly_load import Sb01MinWeeklyLoad

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb01MinWeeklyLoad().validate_preconditions(ctx)
        assert any("omega" in e for e in errors)


# ── SB-02: workload balance ───────────────────────────────────────────────────


class TestSb02WorkloadBalance:
    def test_balance_variables_created(self, built_context):
        from app.solver.constraints.soft.sb02_workload_balance import Sb02WorkloadBalance

        Sb02WorkloadBalance().apply(built_context)
        penalty_sb02 = built_context.get_variable_group("penalty_sb02")

        assert penalty_sb02 is not None
        omega_max, omega_min = penalty_sb02
        assert omega_max is not None
        assert omega_min is not None

    def test_omega_max_gte_omega_min_in_solution(self, built_context):
        from app.solver.constraints.soft.sb02_workload_balance import Sb02WorkloadBalance
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Sb02WorkloadBalance().apply(built_context)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.Solve(built_context.model)

        omega_max = built_context.get_variable_group("omega_max")
        omega_min = built_context.get_variable_group("omega_min")
        assert solver.Value(omega_max) >= solver.Value(omega_min)

    def test_links_omega_max_min_to_omega(self, built_context):
        from app.solver.constraints.soft.sb02_workload_balance import Sb02WorkloadBalance
        from app.solver.constraints.hard.hd01_teacher_assignment import Hd01TeacherAssignment
        from app.solver.constraints.hard.hd02_block_location import Hd02BlockLocation

        Hd01TeacherAssignment().apply(built_context)
        Hd02BlockLocation().apply(built_context)
        Sb02WorkloadBalance().apply(built_context)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.Solve(built_context.model)

        omega = built_context.get_variable_group("omega")
        omega_max = built_context.get_variable_group("omega_max")
        omega_min = built_context.get_variable_group("omega_min")

        max_val = solver.Value(omega_max)
        min_val = solver.Value(omega_min)

        for d_id, omega_var in omega.items():
            val = solver.Value(omega_var)
            assert val <= max_val, f"omega[{d_id}]={val} exceeds omega_max={max_val}"
            assert val >= min_val, f"omega[{d_id}]={val} is below omega_min={min_val}"


# ── SB-05: schedule compactness ───────────────────────────────────────────────


class TestSb05Compactness:
    def test_compactness_penalty_created(self, built_context):
        from app.solver.constraints.soft.sb05_schedule_compactness import Sb05ScheduleCompactness

        Sb05ScheduleCompactness().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb05")
        assert penalty is not None

    def test_gaps_variable_exists(self, built_context):
        """The variable factory should have created gaps[(d, w)] variables."""
        gaps = built_context.get_variable_group("gaps")
        assert gaps is not None
        assert len(gaps) > 0


# ── SB-06: max attendance days ────────────────────────────────────────────────


class TestSb06MaxAttendanceDays:
    def test_excess_days_penalty_created(self, built_context):
        from app.solver.constraints.soft.sb06_max_attendance_days import Sb06MaxAttendanceDays

        Sb06MaxAttendanceDays().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb06")
        assert penalty is not None


# ── SB-03: teacher-group preference ──────────────────────────────────────────


class TestSb03TeacherGroupPreference:
    def test_reward_terms_created(self, built_context):
        from app.solver.constraints.soft.sb03_teacher_group_preference import Sb03TeacherGroupPreference

        count = Sb03TeacherGroupPreference().apply(built_context)
        reward = built_context.get_variable_group("reward_sb03")
        assert reward is not None
        # inst1 has preferences for group1 (8) and group2 (5), so at least 2 terms.
        assert len(reward) >= 2
        # Pure objective term — no constraints added.
        assert count == 0

    def test_reward_entries_have_positive_coefficients(self, built_context):
        from app.solver.constraints.soft.sb03_teacher_group_preference import Sb03TeacherGroupPreference

        Sb03TeacherGroupPreference().apply(built_context)
        reward = built_context.get_variable_group("reward_sb03")
        for _var, coeff in reward:
            assert coeff > 0

    def test_validate_preconditions_missing_X(self, small_problem):
        from app.solver.constraints.soft.sb03_teacher_group_preference import Sb03TeacherGroupPreference

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb03TeacherGroupPreference().validate_preconditions(ctx)
        assert any("X" in e for e in errors)


# ── SB-04: timeslot preference ───────────────────────────────────────────────


class TestSb04TimeslotPreference:
    def test_reward_terms_created(self, built_context):
        from app.solver.constraints.soft.sb04_timeslot_preference import Sb04TimeslotPreference

        count = Sb04TimeslotPreference().apply(built_context)
        reward = built_context.get_variable_group("reward_sb04")
        assert reward is not None
        assert len(reward) > 0
        assert count == 0

    def test_reward_entries_have_positive_coefficients(self, built_context):
        from app.solver.constraints.soft.sb04_timeslot_preference import Sb04TimeslotPreference

        Sb04TimeslotPreference().apply(built_context)
        reward = built_context.get_variable_group("reward_sb04")
        for _var, coeff in reward:
            assert coeff > 0

    def test_validate_preconditions_missing_phi(self, small_problem):
        from app.solver.constraints.soft.sb04_timeslot_preference import Sb04TimeslotPreference

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb04TimeslotPreference().validate_preconditions(ctx)
        assert any("phi" in e for e in errors)


# ── SB-08: weekly distribution ───────────────────────────────────────────────


class TestSb08WeeklyDistribution:
    def test_penalty_created(self, built_context):
        from app.solver.constraints.soft.sb08_weekly_distribution import Sb08WeeklyDistribution

        count = Sb08WeeklyDistribution().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb08")
        assert penalty is not None
        # One rho per instructor that has omega_daily entries.
        assert len(penalty) > 0
        assert count > 0

    def test_rho_bounds_are_valid(self, built_context):
        from app.solver.constraints.soft.sb08_weekly_distribution import Sb08WeeklyDistribution

        Sb08WeeklyDistribution().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb08")
        index = built_context._metadata["index"]

        for d_id, rho_var in penalty.items():
            instructor = index.instructors_by_id[d_id]
            # rho upper bound <= max_daily_periods
            assert rho_var.Proto().domain[-1] <= instructor.max_daily_periods

    def test_validate_preconditions_missing_omega_daily(self, small_problem):
        from app.solver.constraints.soft.sb08_weekly_distribution import Sb08WeeklyDistribution

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb08WeeklyDistribution().validate_preconditions(ctx)
        assert any("omega_daily" in e for e in errors)


# ── SB-09: lunch break ──────────────────────────────────────────────────────


class TestSb09LunchBreak:
    def test_penalty_sb09_registered(self, built_context):
        from app.solver.constraints.soft.sb09_lunch_break import Sb09LunchBreak

        # Use lunch window within our 5-period day: periods 2-4
        count = Sb09LunchBreak(lunch_start=2, lunch_end=4).apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb09")
        assert penalty is not None
        assert count >= 0

    def test_penalty_empty_when_window_out_of_range(self, built_context):
        from app.solver.constraints.soft.sb09_lunch_break import Sb09LunchBreak

        # Lunch window entirely outside available periods (6-8 for a 5-period day)
        count = Sb09LunchBreak(lunch_start=6, lunch_end=8).apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb09")
        assert penalty is not None
        assert count == 0

    def test_validate_preconditions_missing_phi(self, small_problem):
        from app.solver.constraints.soft.sb09_lunch_break import Sb09LunchBreak

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb09LunchBreak().validate_preconditions(ctx)
        assert any("phi" in e for e in errors)


# ── SB-10: room preference ──────────────────────────────────────────────────


class TestSb10RoomPreference:
    def test_reward_terms_created(self, built_context):
        from app.solver.constraints.soft.sb10_room_preference import Sb10RoomPreference

        count = Sb10RoomPreference().apply(built_context)
        reward = built_context.get_variable_group("reward_sb10")
        assert reward is not None
        assert len(reward) > 0
        assert count == 0

    def test_capacity_score_tight_fit(self):
        from app.solver.constraints.soft.sb10_room_preference import Sb10RoomPreference

        # Perfect fit: enrollment=30, capacity=30 -> excess=0 -> score = 5
        score = Sb10RoomPreference._capacity_score(30, 30)
        assert score == 5

    def test_capacity_score_loose_fit(self):
        from app.solver.constraints.soft.sb10_room_preference import Sb10RoomPreference

        # Loose fit: enrollment=20, capacity=80 -> excess=60 -> score = max(1, 5-6) = 1
        score = Sb10RoomPreference._capacity_score(20, 80)
        assert score == 1

    def test_validate_preconditions_missing_R_room(self, small_problem):
        from app.solver.constraints.soft.sb10_room_preference import Sb10RoomPreference

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb10RoomPreference().validate_preconditions(ctx)
        assert any("R_room" in e for e in errors)


# ── SB-11: session concentration ─────────────────────────────────────────────


class TestSb11SessionConcentration:
    def test_penalty_created(self, built_context):
        from app.solver.constraints.soft.sb11_session_concentration import Sb11SessionConcentration

        count = Sb11SessionConcentration().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb11")
        assert penalty is not None
        assert count >= 0

    def test_tau_vars_per_instructor_day(self, built_context):
        from app.solver.constraints.soft.sb11_session_concentration import Sb11SessionConcentration

        Sb11SessionConcentration().apply(built_context)
        penalty = built_context.get_variable_group("penalty_sb11")
        index = built_context._metadata["index"]

        # Each (instructor, day) pair with phi entries should have a tau variable.
        for d_id in index.instructors_by_id:
            for w in index.days:
                key = (d_id, w)
                # tau should exist for each active (instructor, day)
                if key in penalty:
                    tau_var = penalty[key]
                    assert tau_var.Proto().domain[0] >= 0

    def test_validate_preconditions_missing_phi(self, small_problem):
        from app.solver.constraints.soft.sb11_session_concentration import Sb11SessionConcentration

        ctx = OptimizationContext(problem=small_problem, model=cp_model.CpModel())
        errors = Sb11SessionConcentration().validate_preconditions(ctx)
        assert any("phi" in e for e in errors)
