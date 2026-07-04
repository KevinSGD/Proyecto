"""Unit tests for domain value objects."""

from __future__ import annotations

import pytest

from app.core.exceptions.base import DomainError
from app.domain.value_objects import (
    Capacity,
    CreditHours,
    PreferenceScore,
    Semester,
    SessionPattern,
    TimeSlot,
    WorkloadLimits,
    DayOfWeek,
)


class TestCreditHours:
    def test_valid_range(self) -> None:
        assert CreditHours(1).value == 1
        assert CreditHours(12).value == 12

    def test_below_minimum(self) -> None:
        with pytest.raises(DomainError):
            CreditHours(0)

    def test_above_maximum(self) -> None:
        with pytest.raises(DomainError):
            CreditHours(13)


class TestSemester:
    def test_valid_range(self) -> None:
        assert Semester(1).value == 1
        assert Semester(16).value == 16

    def test_below_minimum(self) -> None:
        with pytest.raises(DomainError):
            Semester(0)

    def test_above_maximum(self) -> None:
        with pytest.raises(DomainError):
            Semester(17)


class TestTimeSlot:
    def test_creation(self) -> None:
        slot = TimeSlot(day=DayOfWeek.MONDAY, period=1)
        assert slot.day == DayOfWeek.MONDAY
        assert slot.period == 1

    def test_invalid_period(self) -> None:
        with pytest.raises(DomainError):
            TimeSlot(day=DayOfWeek.MONDAY, period=0)


class TestSessionPattern:
    def test_valid_pattern(self) -> None:
        sp = SessionPattern(credit_hours=4, num_blocks=2, block_durations=(2, 2))
        assert sp.num_blocks == 2

    def test_block_count_mismatch(self) -> None:
        with pytest.raises(DomainError):
            SessionPattern(credit_hours=4, num_blocks=2, block_durations=(4,))

    def test_zero_sum_durations(self) -> None:
        with pytest.raises(DomainError):
            SessionPattern(credit_hours=0, num_blocks=1, block_durations=(0,))


class TestCapacity:
    def test_valid(self) -> None:
        assert Capacity(30).value == 30

    def test_zero_invalid(self) -> None:
        with pytest.raises(DomainError):
            Capacity(0)

    def test_negative_invalid(self) -> None:
        with pytest.raises(DomainError):
            Capacity(-1)


class TestWorkloadLimits:
    def test_valid(self) -> None:
        wl = WorkloadLimits(max_daily_periods=8, max_weekly_periods=40)
        assert wl.min_weekly_periods == 0

    def test_min_exceeds_max(self) -> None:
        with pytest.raises(DomainError):
            WorkloadLimits(
                max_daily_periods=8,
                max_weekly_periods=10,
                min_weekly_periods=20,
            )


class TestPreferenceScore:
    def test_valid_range(self) -> None:
        assert PreferenceScore(0).value == 0
        assert PreferenceScore(10).value == 10

    def test_above_max(self) -> None:
        with pytest.raises(DomainError):
            PreferenceScore(11)

    def test_negative(self) -> None:
        with pytest.raises(DomainError):
            PreferenceScore(-1)
