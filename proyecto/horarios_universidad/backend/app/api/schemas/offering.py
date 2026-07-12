"""Request/response schemas for offering and scheduling entities."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.api.schemas.base import CamelModel


# -- AcademicOffering --------------------------------------------------------


class OfferingCreate(CamelModel):
    institution_id: UUID
    period_id: UUID
    area_id: UUID
    created_by: UUID | None = None


class OfferingUpdate(CamelModel):
    status: str | None = None
    area_id: UUID | None = None


class OfferingOut(CamelModel):
    id: UUID
    institution_id: UUID
    period_id: UUID
    area_id: UUID
    status: str
    created_by: UUID | None


# -- OfferingLine ------------------------------------------------------------


class OfferingLineCreate(CamelModel):
    offering_id: UUID
    subject_id: UUID
    num_groups: int = Field(..., ge=1)
    expected_enrollment_per_group: int = Field(..., ge=1)
    modality: str | None = None
    schedule_type_id: UUID | None = None


class OfferingLineUpdate(CamelModel):
    num_groups: int | None = Field(default=None, ge=1)
    expected_enrollment_per_group: int | None = Field(default=None, ge=1)
    modality: str | None = None
    schedule_type_id: UUID | None = None


class OfferingLineOut(CamelModel):
    id: UUID
    offering_id: UUID
    subject_id: UUID
    num_groups: int
    expected_enrollment_per_group: int
    modality: str
    schedule_type_id: UUID | None


class OfferingDetail(OfferingOut):
    """Offering with its nested lines."""

    lines: list[OfferingLineOut] = Field(default_factory=list)


# -- ScheduleType ------------------------------------------------------------


class ScheduleTypeCreate(CamelModel):
    institution_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    schedule_type: str = Field(..., min_length=1, max_length=100)
    active_days: list[int]
    start_period: int = Field(..., ge=0)
    end_period: int = Field(..., ge=0)
    slot_duration_minutes: int | None = None


class ScheduleTypeUpdate(CamelModel):
    name: str | None = None
    schedule_type: str | None = None
    active_days: list[int] | None = None
    start_period: int | None = Field(default=None, ge=0)
    end_period: int | None = Field(default=None, ge=0)
    slot_duration_minutes: int | None = None


class ScheduleTypeOut(CamelModel):
    id: UUID
    institution_id: UUID
    name: str
    schedule_type: str
    active_days: list[int]
    start_period: int
    end_period: int
    slot_duration_minutes: int


# -- Group -------------------------------------------------------------------


class GroupCreate(CamelModel):
    offering_line_id: UUID
    subject_id: UUID
    group_number: int = Field(..., ge=1)
    expected_enrollment: int = Field(..., ge=0)
    modality: str
    schedule_type_id: UUID
    priority: int | None = None


class GroupOut(CamelModel):
    id: UUID
    offering_line_id: UUID
    subject_id: UUID
    group_number: int
    expected_enrollment: int
    modality: str
    schedule_type_id: UUID
    priority: int
