"""Domain-specific identifier type aliases."""

from __future__ import annotations

from app.core.utils.types import EntityId

__all__ = [
    "EntityId",
    "InstitutionId",
    "AreaId",
    "SubjectId",
    "GroupId",
    "InstructorId",
    "ClassroomId",
    "UserId",
]

InstitutionId = EntityId
AreaId = EntityId
SubjectId = EntityId
GroupId = EntityId
InstructorId = EntityId
ClassroomId = EntityId
UserId = EntityId
