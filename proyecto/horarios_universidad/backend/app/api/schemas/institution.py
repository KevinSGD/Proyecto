"""Request/response schemas for institution entities."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from app.api.schemas.base import CamelModel


# ── Institution ──────────────────────────────────────────────────────────────


class InstitutionCreate(CamelModel):
    name: str = Field(..., min_length=1, max_length=200, examples=["Universidad Nacional"])
    abbreviation: str = Field(..., min_length=1, max_length=20, examples=["UN"])
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    logo_url: str | None = None


class InstitutionUpdate(CamelModel):
    name: str | None = None
    abbreviation: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    logo_url: str | None = None


class InstitutionOut(CamelModel):
    id: UUID
    name: str
    abbreviation: str
    address: str
    email: str
    phone: str
    website: str
    logo_url: str
    is_active: bool


# ── Campus ───────────────────────────────────────────────────────────────────


class CampusOut(CamelModel):
    id: UUID
    institution_id: UUID
    name: str
    code: str
    address: str
    city: str
    is_active: bool


# ── Academic Period ──────────────────────────────────────────────────────────


class AcademicPeriodCreate(CamelModel):
    institution_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    year: int = Field(..., ge=2000, le=2100)
    period_number: int = Field(..., ge=1)
    start_date: date | None = None
    end_date: date | None = None


class AcademicPeriodOut(CamelModel):
    id: UUID
    institution_id: UUID
    name: str
    year: int
    period_number: int
    status: str
    is_active: bool
    start_date: date | None
    end_date: date | None
