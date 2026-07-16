"""Personnel entities (instructors and their attributes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "Instructor",
    "InstructorContract",
    "InstructorSpecialty",
    "InstructorQualification",
    "InstructorAvailability",
    "InstructorPreference",
]


@dataclass
class Instructor:
    """A teaching staff member."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    area_id: EntityId | None = None
    employee_code: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    is_active: bool = True


@dataclass
class InstructorContract:
    """Employment contract defining workload limits for an instructor."""

    id: EntityId = field(default_factory=generate_id)
    instructor_id: EntityId = field(default_factory=generate_id)
    contract_type: str = ""
    start_date: date | None = None
    end_date: date | None = None
    max_daily_periods: int = 0
    max_weekly_periods: int = 0
    min_weekly_periods: int = 0
    max_days: int | None = None
    is_active: bool = True


@dataclass
class InstructorSpecialty:
    """Links an instructor to a subject they are qualified to teach."""

    id: EntityId = field(default_factory=generate_id)
    instructor_id: EntityId = field(default_factory=generate_id)
    subject_id: EntityId = field(default_factory=generate_id)
    proficiency_level: int = 5


@dataclass
class InstructorQualification:
    """Academic or professional credential held by an instructor."""

    id: EntityId = field(default_factory=generate_id)
    instructor_id: EntityId = field(default_factory=generate_id)
    qualification_type: str = ""
    title: str = ""
    institution_name: str = ""
    year_obtained: int | None = None


@dataclass
class InstructorAvailability:
    """Per-slot availability for an instructor."""

    id: EntityId = field(default_factory=generate_id)
    instructor_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId | None = None
    day_of_week: int = 0
    period: int = 0
    is_available: bool = True


@dataclass
class InstructorPreference:
    """Instructor preference for a specific group or subject."""

    id: EntityId = field(default_factory=generate_id)
    instructor_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId | None = None
    group_id: EntityId | None = None
    subject_id: EntityId | None = None
    score: int = 5
