"""Academic offering entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "AcademicOffering",
    "OfferingLine",
]


@dataclass
class AcademicOffering:
    """A batch of subjects offered for a specific academic period."""

    id: EntityId = field(default_factory=generate_id)
    institution_id: EntityId = field(default_factory=generate_id)
    period_id: EntityId = field(default_factory=generate_id)
    area_id: EntityId = field(default_factory=generate_id)
    status: str = "draft"
    created_by: EntityId | None = None


@dataclass
class OfferingLine:
    """A single subject line within an academic offering."""

    id: EntityId = field(default_factory=generate_id)
    offering_id: EntityId = field(default_factory=generate_id)
    subject_id: EntityId = field(default_factory=generate_id)
    num_groups: int = 0
    expected_enrollment_per_group: int = 0
    modality: str = "presential"
    schedule_type_id: EntityId | None = None
