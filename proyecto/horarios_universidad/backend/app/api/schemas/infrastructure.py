"""Pydantic schemas for infrastructure API endpoints."""

from __future__ import annotations

from uuid import UUID

from app.api.schemas.base import CamelModel


# ── Building ─────────────────────────────────────────────────────────────────


class BuildingCreate(CamelModel):
    campus_id: UUID
    name: str
    code: str
    floors: int = 1


class BuildingUpdate(CamelModel):
    name: str | None = None
    code: str | None = None
    floors: int | None = None
    is_active: bool | None = None


class BuildingOut(CamelModel):
    id: UUID
    campus_id: UUID
    name: str
    code: str
    floors: int
    is_active: bool


# ── Classroom ────────────────────────────────────────────────────────────────


class ClassroomCreate(CamelModel):
    institution_id: UUID
    building_id: UUID | None = None
    name: str
    code: str
    capacity: int
    floor: int | None = None
    is_virtual: bool = False


class ClassroomUpdate(CamelModel):
    name: str | None = None
    code: str | None = None
    capacity: int | None = None
    floor: int | None = None
    is_virtual: bool | None = None
    is_active: bool | None = None
    building_id: UUID | None = None


class ClassroomOut(CamelModel):
    id: UUID
    institution_id: UUID
    building_id: UUID | None = None
    name: str
    code: str
    capacity: int
    floor: int | None = None
    is_virtual: bool
    is_active: bool


# ── Classroom availability ───────────────────────────────────────────────────


class ClassroomAvailSlot(CamelModel):
    day_of_week: int
    period: int
    is_available: bool = True


class ClassroomAvailBulkSet(CamelModel):
    classroom_id: UUID
    period_id: UUID | None = None
    slots: list[ClassroomAvailSlot]


class AvailabilityBulkBody(CamelModel):
    """Request body for PUT /classrooms/{id}/availability."""

    period_id: UUID | None = None
    slots: list[ClassroomAvailSlot]


class ClassroomAvailOut(CamelModel):
    id: UUID
    classroom_id: UUID
    period_id: UUID | None = None
    day_of_week: int
    period: int
    is_available: bool


# ── Resource ────────────────────────────────────────────────────────────────


class ResourceCreate(CamelModel):
    institution_id: UUID
    name: str
    code: str
    description: str = ""
    is_active: bool = True


class ResourceUpdate(CamelModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ResourceOut(CamelModel):
    id: UUID
    institution_id: UUID
    name: str
    code: str
    description: str
    is_active: bool = True


# ── Room resource ──────────────────────────────────────────────────────────


class RoomResourceCreate(CamelModel):
    classroom_id: UUID
    resource_id: UUID
    quantity: int = 1


class ResourceAssignBody(CamelModel):
    """Request body for POST /classrooms/{id}/resources."""

    resource_id: UUID
    quantity: int = 1


class RoomResourceOut(CamelModel):
    id: UUID
    classroom_id: UUID
    resource_id: UUID
    quantity: int


# ── Subject resource requirement ──────────────────────────────────────────


class SubjectResourceBody(CamelModel):
    """Request body for POST /subjects/{id}/resources."""

    resource_id: UUID
    is_mandatory: bool = True


class SubjectResourceOut(CamelModel):
    id: UUID
    subject_id: UUID
    resource_id: UUID
    is_mandatory: bool
