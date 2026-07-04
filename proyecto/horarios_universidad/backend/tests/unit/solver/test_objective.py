"""Unit tests for objective components F1 through F6 — Doc 07.

Each test constructs a minimal OptimizationContext and verifies that the
compute_terms method returns the expected (variable, coefficient) pairs without
errors.
"""

from __future__ import annotations

import gc

import pytest

pytest.importorskip("ortools", reason="ortools not installed")

# Disable GC to avoid Python 3.14 + ortools heap corruption (0xc0000374)
# during CpModel finalisation in `_add_pre_pep8_methods`.
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
from app.solver.objective.base import ObjectiveInfo  # noqa: E402
from app.solver.preprocessing.index_builder import build_indices  # noqa: E402
from app.solver.variables.factory import VariableFactory  # noqa: E402


# ── shared helpers ───────────────────────────────────────────────────────────


def _make_ids():
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


def _make_small_problem(ids) -> OptimizationProblem:
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


def _build_context() -> OptimizationContext:
    ids = _make_ids()
    problem = _make_small_problem(ids)
    model = cp_model.CpModel()
    index = build_indices(problem)
    context = OptimizationContext(problem=problem, model=model)
    context._metadata["index"] = index
    VariableFactory().create_all(model, problem, index, context)
    return context


# ── F1: workload balance ─────────────────────────────────────────────────────


class TestF1WorkloadBalance:
    def test_info_is_objective_info(self):
        from app.solver.objective.components.f1_workload_balance import F1WorkloadBalance

        obj = F1WorkloadBalance()
        assert isinstance(obj.info, ObjectiveInfo)
        assert obj.info.name == "F1"
        assert obj.info.weight == 50

    def test_f1_balance_terms(self):
        from app.solver.objective.components.f1_workload_balance import F1WorkloadBalance

        ctx = _build_context()
        obj = F1WorkloadBalance()
        errors = obj.validate_preconditions(ctx)
        assert errors == []

        terms = obj.compute_terms(ctx)
        assert len(terms) == 2

        # omega_max term must have coefficient -1; omega_min must have +1.
        coefficients = {coeff for _, coeff in terms}
        assert -1 in coefficients
        assert 1 in coefficients

    def test_f1_returns_correct_variables(self):
        from app.solver.objective.components.f1_workload_balance import F1WorkloadBalance

        ctx = _build_context()
        terms = F1WorkloadBalance().compute_terms(ctx)

        omega_max = ctx.get_variable_group("omega_max")
        omega_min = ctx.get_variable_group("omega_min")

        term_vars = [var for var, _ in terms]
        assert omega_max in term_vars
        assert omega_min in term_vars

    def test_f1_empty_when_missing_vars(self):
        from app.solver.objective.components.f1_workload_balance import F1WorkloadBalance

        ids = _make_ids()
        problem = _make_small_problem(ids)
        ctx = OptimizationContext(problem=problem, model=cp_model.CpModel())
        terms = F1WorkloadBalance().compute_terms(ctx)
        assert terms == []


# ── F2: teacher-group preference ─────────────────────────────────────────────


class TestF2TeacherGroupPreference:
    def test_f2_preference_terms(self):
        from app.solver.objective.components.f2_teacher_group_preference import (
            F2TeacherGroupPreference,
        )

        ctx = _build_context()
        obj = F2TeacherGroupPreference()
        terms = obj.compute_terms(ctx)

        # The two instructors together have positive preferences; terms must be non-empty.
        assert len(terms) > 0

    def test_f2_terms_match_preference_scores(self):
        from app.solver.objective.components.f2_teacher_group_preference import (
            F2TeacherGroupPreference,
        )

        ctx = _build_context()
        terms = F2TeacherGroupPreference().compute_terms(ctx)

        # All coefficients must be positive integers (preference scores).
        for _, coeff in terms:
            assert isinstance(coeff, int)
            assert coeff > 0

    def test_f2_reuses_reward_sb03_when_present(self):
        from app.solver.objective.components.f2_teacher_group_preference import (
            F2TeacherGroupPreference,
        )
        from app.solver.constraints.soft.sb03_teacher_group_preference import (
            Sb03TeacherGroupPreference,
        )

        ctx = _build_context()
        Sb03TeacherGroupPreference().apply(ctx)
        reward = ctx.get_variable_group("reward_sb03")
        assert reward is not None

        terms = F2TeacherGroupPreference().compute_terms(ctx)
        # When reward_sb03 is present, terms should equal it directly.
        assert terms == list(reward)

    def test_f2_info(self):
        from app.solver.objective.components.f2_teacher_group_preference import (
            F2TeacherGroupPreference,
        )

        obj = F2TeacherGroupPreference()
        assert obj.info.name == "F2"
        assert obj.info.weight == 30


# ── F3: timeslot preference ───────────────────────────────────────────────────


class TestF3TimeslotPreference:
    def test_f3_terms_exist_with_phi(self):
        from app.solver.objective.components.f3_timeslot_preference import (
            F3TimeslotPreference,
        )

        ctx = _build_context()
        terms = F3TimeslotPreference().compute_terms(ctx)
        # All slots are available, so every phi variable becomes a term.
        assert len(terms) > 0

    def test_f3_reuses_reward_sb04(self):
        from app.solver.objective.components.f3_timeslot_preference import (
            F3TimeslotPreference,
        )
        from app.solver.constraints.soft.sb04_timeslot_preference import (
            Sb04TimeslotPreference,
        )

        ctx = _build_context()
        Sb04TimeslotPreference().apply(ctx)
        reward = ctx.get_variable_group("reward_sb04")
        assert reward is not None

        terms = F3TimeslotPreference().compute_terms(ctx)
        assert terms == list(reward)


# ── F4: schedule compactness ─────────────────────────────────────────────────


class TestF4ScheduleCompactness:
    def test_f4_terms_from_gaps(self):
        from app.solver.objective.components.f4_schedule_compactness import (
            F4ScheduleCompactness,
        )

        ctx = _build_context()
        terms = F4ScheduleCompactness().compute_terms(ctx)

        # All terms must have coefficient -1.
        assert len(terms) > 0
        for _, coeff in terms:
            assert coeff == -1

    def test_f4_prefers_penalty_sb05(self):
        from app.solver.objective.components.f4_schedule_compactness import (
            F4ScheduleCompactness,
        )

        ctx = _build_context()
        # Register a fake penalty_sb05 to verify it takes precedence.
        model: cp_model.CpModel = ctx.model
        fake_penalty = {generate_id(): model.NewIntVar(0, 10, "fake_sb05")}
        ctx.add_variable_group("penalty_sb05", fake_penalty)

        terms = F4ScheduleCompactness().compute_terms(ctx)
        term_vars = [var for var, _ in terms]
        assert list(fake_penalty.values())[0] in term_vars


# ── F5: soft penalties ───────────────────────────────────────────────────────


class TestF5SoftPenalties:
    def test_f5_no_error_when_no_penalties(self):
        from app.solver.objective.components.f5_soft_penalties import F5SoftPenalties

        ctx = _build_context()
        errors = F5SoftPenalties().validate_preconditions(ctx)
        assert errors == []

        terms = F5SoftPenalties().compute_terms(ctx)
        # No penalty groups registered — result should be empty.
        assert terms == []

    def test_f5_collects_penalty_sb01(self):
        from app.solver.constraints.soft.sb01_min_weekly_load import Sb01MinWeeklyLoad
        from app.solver.objective.components.f5_soft_penalties import F5SoftPenalties

        ctx = _build_context()
        Sb01MinWeeklyLoad().apply(ctx)

        terms = F5SoftPenalties().compute_terms(ctx)
        assert len(terms) > 0
        # All terms from penalty_sb01 must have negative coefficients.
        for _, coeff in terms:
            assert coeff < 0

    def test_f5_collects_reward_sb03(self):
        from app.solver.constraints.soft.sb03_teacher_group_preference import (
            Sb03TeacherGroupPreference,
        )
        from app.solver.objective.components.f5_soft_penalties import F5SoftPenalties

        ctx = _build_context()
        Sb03TeacherGroupPreference().apply(ctx)

        terms = F5SoftPenalties().compute_terms(ctx)
        # reward_sb03 contributes positive coefficients.
        positive = [coeff for _, coeff in terms if coeff > 0]
        assert len(positive) > 0

    def test_f5_handles_penalty_sb02_tuple(self):
        from app.solver.constraints.soft.sb02_workload_balance import Sb02WorkloadBalance
        from app.solver.objective.components.f5_soft_penalties import F5SoftPenalties

        ctx = _build_context()
        Sb02WorkloadBalance().apply(ctx)

        terms = F5SoftPenalties().compute_terms(ctx)
        # penalty_sb02 is a (omega_max, omega_min) tuple — should contribute 2 terms.
        omega_max = ctx.get_variable_group("omega_max")
        omega_min = ctx.get_variable_group("omega_min")
        term_vars = [var for var, _ in terms]
        assert omega_max in term_vars
        assert omega_min in term_vars


# ── F6: room utilisation ─────────────────────────────────────────────────────


class TestF6RoomUtilization:
    def test_f6_creates_u_max_u_min_terms(self):
        from app.solver.objective.components.f6_room_utilization import F6RoomUtilization

        ctx = _build_context()
        terms = F6RoomUtilization().compute_terms(ctx)

        assert len(terms) == 2
        coefficients = {coeff for _, coeff in terms}
        assert -1 in coefficients
        assert 1 in coefficients

    def test_f6_validate_missing_z(self):
        from app.solver.objective.components.f6_room_utilization import F6RoomUtilization

        ids = _make_ids()
        problem = _make_small_problem(ids)
        ctx = OptimizationContext(problem=problem, model=cp_model.CpModel())
        errors = F6RoomUtilization().validate_preconditions(ctx)
        assert any("Z" in e for e in errors)


# ── all components produce terms ─────────────────────────────────────────────


class TestAllComponentsProduceTerms:
    def test_all_components_produce_terms(self):
        from app.solver.objective.components.f1_workload_balance import F1WorkloadBalance
        from app.solver.objective.components.f2_teacher_group_preference import (
            F2TeacherGroupPreference,
        )
        from app.solver.objective.components.f3_timeslot_preference import (
            F3TimeslotPreference,
        )
        from app.solver.objective.components.f4_schedule_compactness import (
            F4ScheduleCompactness,
        )
        from app.solver.objective.components.f5_soft_penalties import F5SoftPenalties
        from app.solver.objective.components.f6_room_utilization import F6RoomUtilization
        from app.solver.constraints.soft.sb01_min_weekly_load import Sb01MinWeeklyLoad
        from app.solver.constraints.soft.sb02_workload_balance import Sb02WorkloadBalance

        ctx = _build_context()

        # Register some soft constraints so F5 has material to work with.
        Sb01MinWeeklyLoad().apply(ctx)
        Sb02WorkloadBalance().apply(ctx)

        components = [
            F1WorkloadBalance(),
            F2TeacherGroupPreference(),
            F3TimeslotPreference(),
            F4ScheduleCompactness(),
            F5SoftPenalties(),
            F6RoomUtilization(),
        ]

        for comp in components:
            errors = comp.validate_preconditions(ctx)
            assert errors == [], f"{comp.info.name} failed preconditions: {errors}"
            terms = comp.compute_terms(ctx)
            assert isinstance(terms, list), f"{comp.info.name}.compute_terms must return list"

    def test_component_info_fields(self):
        from app.solver.objective.components import (
            F1WorkloadBalance,
            F2TeacherGroupPreference,
            F3TimeslotPreference,
            F4ScheduleCompactness,
            F5SoftPenalties,
            F6RoomUtilization,
        )

        for cls in [
            F1WorkloadBalance,
            F2TeacherGroupPreference,
            F3TimeslotPreference,
            F4ScheduleCompactness,
            F5SoftPenalties,
            F6RoomUtilization,
        ]:
            obj = cls()
            info = obj.info
            assert info.name
            assert info.description
            assert info.weight > 0
            assert isinstance(info.is_enabled, bool)
