"""Physical infrastructure entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "Building",
    "Classroom",
    "ClassroomAvailability",
    "Resource",
    "RoomResource",
    "SubjectResourceRequirement",
]


@dataclass
class Building:
    """A physical building on a campus."""

    id: EntityId = field(default_factory=generate_id)
    campus_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    code: str = ""
    floors: int = 1
    is_active: bool = True


@dataclass
class Classroom:
    """A physical or virtual room where classes can be held."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    building_id: EntityId | None = None
    name: str = ""
    code: str = ""
    capacity: int = 0
    floor: int | None = None
    is_virtual: bool = False
    is_active: bool = True


@dataclass
class ClassroomAvailability:
    """Per-slot availability for a classroom."""

    id: EntityId = field(default_factory=generate_id)
    classroom_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId | None = None
    day_of_week: int = 0
    period: int = 0
    is_available: bool = True


@dataclass
class Resource:
    """A resource available in the institution (projector, whiteboard, etc.)."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    code: str = ""
    description: str = ""
    is_active: bool = True


@dataclass
class RoomResource:
    """Association between a classroom and its available resources."""

    id: EntityId = field(default_factory=generate_id)
    classroom_id: EntityId = field(default_factory=generate_id)
    resource_id: EntityId = field(default_factory=generate_id)
    quantity: int = 1


@dataclass
class SubjectResourceRequirement:
    """Resource required by a subject."""

    id: EntityId = field(default_factory=generate_id)
    subject_id: EntityId = field(default_factory=generate_id)
    resource_id: EntityId = field(default_factory=generate_id)
    is_mandatory: bool = True
