"""Unit tests for the validation pipeline."""

from __future__ import annotations

import uuid

import pytest

from app.domain.interfaces.validation import ValidationResult
from app.solver.context import (
    OptimizationProblem,
    SolverGroup,
    SolverTimeConfig,
)
from app.solver.validator.base import AbstractSolverValidator
from app.solver.validator.pipeline import SolverValidationPipeline


# ── helpers ──────────────────────────────────────────────────────────────


class _AlwaysOkValidator(AbstractSolverValidator):
    @property
    def name(self) -> str:
        return "always_ok"

    def validate(self, problem: OptimizationProblem) -> ValidationResult:
        return ValidationResult.ok()


class _AlwaysFailValidator(AbstractSolverValidator):
    def __init__(self, error_msg: str = "boom") -> None:
        self._msg = error_msg

    @property
    def name(self) -> str:
        return "always_fail"

    def validate(self, problem: OptimizationProblem) -> ValidationResult:
        return ValidationResult.fail(self._msg)


def _uid() -> uuid.UUID:
    return uuid.uuid4()


def _empty_problem() -> OptimizationProblem:
    return OptimizationProblem(institution_id=_uid(), period_id=_uid())


# ── ValidationResult tests ──────────────────────────────────────────────


class TestValidationResult:
    def test_ok(self) -> None:
        r = ValidationResult.ok()
        assert r.is_valid is True
        assert r.errors == []

    def test_fail(self) -> None:
        r = ValidationResult.fail("bad data")
        assert r.is_valid is False
        assert "bad data" in r.errors

    def test_merge(self) -> None:
        a = ValidationResult.ok()
        a.add_warning("heads up")
        b = ValidationResult.fail("oops")
        a.merge(b)
        assert a.is_valid is False
        assert len(a.errors) == 1
        assert len(a.warnings) == 1


# ── SolverValidationPipeline tests ──────────────────────────────────────


class TestSolverValidationPipeline:
    def test_empty_pipeline_passes(self) -> None:
        pipe = SolverValidationPipeline()
        result = pipe.validate(_empty_problem())
        assert result.is_valid is True

    def test_with_ok_validator(self) -> None:
        pipe = SolverValidationPipeline()
        pipe.add_validator(_AlwaysOkValidator())
        result = pipe.validate(_empty_problem())
        assert result.is_valid is True

    def test_with_failing_validator(self) -> None:
        pipe = SolverValidationPipeline()
        pipe.add_validator(_AlwaysFailValidator("invalid input"))
        result = pipe.validate(_empty_problem())
        assert result.is_valid is False
        assert "invalid input" in result.errors

    def test_multiple_validators_merge(self) -> None:
        pipe = SolverValidationPipeline()
        pipe.add_validator(_AlwaysOkValidator())
        pipe.add_validator(_AlwaysFailValidator("err1"))
        result = pipe.validate(_empty_problem())
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_builtin_no_candidate_instructors(self) -> None:
        problem = _empty_problem()
        problem.groups.append(
            SolverGroup(
                id=_uid(),
                subject_id=_uid(),
                group_number=1,
                expected_enrollment=30,
                modality="presential",
                schedule_type_id=_uid(),
                num_blocks=1,
                block_durations=(2,),
                candidate_instructors=[],
                compatible_classrooms=[_uid()],
            )
        )
        pipe = SolverValidationPipeline()
        result = pipe.validate(problem)
        assert result.is_valid is False
        assert any("no candidate instructors" in e for e in result.errors)

    def test_builtin_no_classrooms_for_presential(self) -> None:
        problem = _empty_problem()
        problem.groups.append(
            SolverGroup(
                id=_uid(),
                subject_id=_uid(),
                group_number=1,
                expected_enrollment=30,
                modality="presential",
                schedule_type_id=_uid(),
                num_blocks=1,
                block_durations=(2,),
                candidate_instructors=[_uid()],
                compatible_classrooms=[],
            )
        )
        pipe = SolverValidationPipeline()
        result = pipe.validate(problem)
        assert result.is_valid is False
        assert any("no compatible classrooms" in e for e in result.errors)

    def test_builtin_block_duration_exceeds_periods(self) -> None:
        problem = _empty_problem()
        problem.time_config = SolverTimeConfig(
            days=[1, 2, 3], periods_per_day=6
        )
        problem.groups.append(
            SolverGroup(
                id=_uid(),
                subject_id=_uid(),
                group_number=1,
                expected_enrollment=20,
                modality="virtual",
                schedule_type_id=_uid(),
                num_blocks=1,
                block_durations=(8,),
                candidate_instructors=[_uid()],
            )
        )
        pipe = SolverValidationPipeline()
        result = pipe.validate(problem)
        assert result.is_valid is False
        assert any("exceeds periods_per_day" in e for e in result.errors)

    def test_virtual_group_no_classroom_ok(self) -> None:
        problem = _empty_problem()
        problem.groups.append(
            SolverGroup(
                id=_uid(),
                subject_id=_uid(),
                group_number=1,
                expected_enrollment=30,
                modality="virtual",
                schedule_type_id=_uid(),
                num_blocks=1,
                block_durations=(2,),
                candidate_instructors=[_uid()],
                compatible_classrooms=[],
            )
        )
        pipe = SolverValidationPipeline()
        result = pipe.validate(problem)
        assert result.is_valid is True
