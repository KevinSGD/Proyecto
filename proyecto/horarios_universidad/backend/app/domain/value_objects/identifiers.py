"""Domain-specific identifier type aliases."""

from __future__ import annotations

from app.core.utils.types import EntityId

__all__ = [
    "EntityId",
    "InstitutionId",
    "AreaId",
    "ProgramId",
    "SubjectId",
    "GroupId",
    "InstructorId",
    "ClassroomId",
    "UserId",
]

InstitutionId = EntityId
AreaId = EntityId
ProgramId = EntityId
SubjectId = EntityId
GroupId = EntityId
InstructorId = EntityId
ClassroomId = EntityId
UserId = EntityId
