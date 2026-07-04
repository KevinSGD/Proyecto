"""Domain value objects."""

from app.domain.value_objects.academic import (
    CreditHours,
    Modality,
    Semester,
    SubjectCategory,
)
from app.domain.value_objects.capacity import (
    Capacity,
    Enrollment,
    is_compatible,
)
from app.domain.value_objects.contract import (
    ContractType,
    WorkloadLimits,
)
from app.domain.value_objects.identifiers import (
    AreaId,
    ClassroomId,
    EntityId,
    GroupId,
    InstitutionId,
    InstructorId,
    ProgramId,
    SubjectId,
    UserId,
)
from app.domain.value_objects.preference import (
    PreferenceScore,
    Priority,
    Weight,
)
from app.domain.value_objects.temporal import (
    DayOfWeek,
    ScheduleTypeName,
    SessionPattern,
    TimeRange,
    TimeSlot,
)

__all__ = [
    # identifiers
    "EntityId",
    "InstitutionId",
    "AreaId",
    "ProgramId",
    "SubjectId",
    "GroupId",
    "InstructorId",
    "ClassroomId",
    "UserId",
    # academic
    "CreditHours",
    "Semester",
    "Modality",
    "SubjectCategory",
    # temporal
    "DayOfWeek",
    "TimeSlot",
    "TimeRange",
    "SessionPattern",
    "ScheduleTypeName",
    # capacity
    "Capacity",
    "Enrollment",
    "is_compatible",
    # preference
    "PreferenceScore",
    "Priority",
    "Weight",
    # contract
    "ContractType",
    "WorkloadLimits",
]
