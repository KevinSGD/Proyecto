"""Request/response schemas for academic entities."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.api.schemas.base import CamelModel


# ── Academic Area ────────────────────────────────────────────────────────────


class CoordinatorCreate(CamelModel):
    email: str = Field(..., min_length=5, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class AreaCreate(CamelModel):
    institution_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    coordinator: CoordinatorCreate


class AreaUpdate(CamelModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CoordinatorOut(CamelModel):
    user_id: UUID
    email: str
    name: str


class AreaOut(CamelModel):
    id: UUID
    institution_id: UUID
    name: str
    code: str
    description: str
    is_active: bool
    coordinator: CoordinatorOut | None = None


# ── Subject ──────────────────────────────────────────────────────────────────


class SubjectCreate(CamelModel):
    institution_id: UUID
    area_id: UUID | None = None
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    credit_hours: int = Field(..., ge=0)
    weekly_hours: int = Field(..., ge=0)
    modality_default: str = "presential"


class SubjectUpdate(CamelModel):
    area_id: UUID | None = None
    code: str | None = None
    name: str | None = None
    credit_hours: int | None = None
    weekly_hours: int | None = None
    modality_default: str | None = None
    is_active: bool | None = None


class SubjectOut(CamelModel):
    id: UUID
    institution_id: UUID
    area_id: UUID | None = None
    code: str
    name: str
    credit_hours: int
    weekly_hours: int
    modality_default: str
    is_active: bool
