"""Institution, campus, and academic-period entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "Institution",
    "Campus",
    "AcademicPeriod",
]


@dataclass
class Institution:
    """A university or educational institution."""

    id: EntityId = field(default_factory=generate_id)
    name: str = ""
    abbreviation: str = ""
    address: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    logo_url: str = ""
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Campus:
    """A physical location belonging to an institution."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    code: str = ""
    address: str = ""
    city: str = ""
    is_active: bool = True


@dataclass
class AcademicPeriod:
    """A specific academic term within an institution."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    year: int = 0
    period_number: int = 0
    status: str = "draft"
    is_active: bool = True
    start_date: date | None = None
    end_date: date | None = None
