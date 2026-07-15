"""Pydantic schemas for personnel (instructor) API endpoints."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from app.api.schemas.base import CamelModel

__all__ = [
    "InstructorCreate",
    "InstructorUpdate",
    "InstructorOut",
    "InstructorDetail",
    "ContractCreate",
    "ContractUpdate",
    "ContractOut",
    "SpecialtyCreate",
    "SpecialtyOut",
    "QualificationOut",
    "AvailabilitySlot",
    "AvailabilityBulkSet",
    "AvailabilityOut",
    "PreferenceCreate",
    "PreferenceOut",
]


# ── Contract ─────────────────────────────────────────────────────────────────


class ContractCreate(CamelModel):
    """Payload to create an instructor contract."""

    instructor_id: UUID
    contract_type: str
    start_date: date | None = None
    end_date: date | None = None
    max_daily_periods: int
    max_weekly_periods: int
    min_weekly_periods: int
    max_days: int | None = None


class ContractUpdate(CamelModel):
    """Partial update for an instructor contract."""

    contract_type: str | None = None
    max_daily_periods: int | None = None
    max_weekly_periods: int | None = None
    min_weekly_periods: int | None = None
    max_days: int | None = None
    is_active: bool | None = None


class ContractOut(CamelModel):
    """Public representation of an instructor contract."""

    id: UUID
    instructor_id: UUID
    contract_type: str
    start_date: date | None = None
    end_date: date | None = None
    max_daily_periods: int
    max_weekly_periods: int
    min_weekly_periods: int
    max_days: int | None = None
    is_active: bool


# ── Specialty ────────────────────────────────────────────────────────────────


class SpecialtyCreate(CamelModel):
    """Payload to link an instructor to a subject."""

    instructor_id: UUID
    subject_id: UUID
    proficiency_level: int = 5


class SpecialtyOut(CamelModel):
    """Public representation of an instructor specialty."""

    id: UUID
    instructor_id: UUID
    subject_id: UUID
    proficiency_level: int


# ── Qualification ────────────────────────────────────────────────────────────


class QualificationOut(CamelModel):
    """Public representation of an instructor qualification."""

    id: UUID
    instructor_id: UUID
    qualification_type: str
    title: str
    institution_name: str
    year_obtained: int | None = None


# ── Availability ─────────────────────────────────────────────────────────────


class AvailabilitySlot(CamelModel):
    """A single time-slot availability entry."""

    day_of_week: int
    period: int
    is_available: bool = True


class AvailabilityBulkSet(CamelModel):
    """Bulk-set availability slots for an instructor."""

    instructor_id: UUID
    period_id: UUID | None = None
    slots: list[AvailabilitySlot]


class AvailabilityOut(CamelModel):
    """Public representation of an instructor availability slot."""

    id: UUID
    instructor_id: UUID
    period_id: UUID | None = None
    day_of_week: int
    period: int
    is_available: bool


# ── Preference ───────────────────────────────────────────────────────────────


class PreferenceCreate(CamelModel):
    """Payload to set an instructor preference."""

    instructor_id: UUID
    period_id: UUID | None = None
    group_id: UUID | None = None
    subject_id: UUID | None = None
    score: int = 5


class PreferenceOut(CamelModel):
    """Public representation of an instructor preference."""

    id: UUID
    instructor_id: UUID
    period_id: UUID | None = None
    group_id: UUID | None = None
    subject_id: UUID | None = None
    score: int


# ── Instructor ───────────────────────────────────────────────────────────────


class InstructorCreate(CamelModel):
    """Payload to register a new instructor."""

    institution_id: UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None


class InstructorUpdate(CamelModel):
    """Partial update for an existing instructor."""

    employee_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class InstructorOut(CamelModel):
    """Public representation of an instructor."""

    id: UUID
    institution_id: UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: str
    is_active: bool
    contract_type: str | None = None
    max_weekly_hours: int | None = None


class InstructorDetail(InstructorOut):
    """Instructor with related contracts, specialties, and qualifications."""

    contracts: list[ContractOut] = Field(default_factory=list)
    specialties: list[SpecialtyOut] = Field(default_factory=list)
    qualifications: list[QualificationOut] = Field(default_factory=list)
