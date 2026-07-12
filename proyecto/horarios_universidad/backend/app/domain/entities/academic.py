"""Academic structure entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "AcademicArea",
    "Subject",
]


@dataclass
class AcademicArea:
    """An academic division within an institution (e.g. Engineering)."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    code: str = ""
    description: str = ""
    is_active: bool = True


@dataclass
class Subject:
    """A course or subject offered by the institution."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    code: str = ""
    name: str = ""
    credit_hours: int = 0
    weekly_hours: int = 0
    modality_default: str = "presential"
    is_active: bool = True
