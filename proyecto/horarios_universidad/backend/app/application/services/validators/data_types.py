"""Data containers for domain validation.

Each dataclass packages the pre-loaded entities that a specific validator
needs so the validator itself stays repository-free and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.entities.academic import PlanSubject, Subject, SubjectPrerequisite
from app.domain.entities.infrastructure import (
    Classroom,
    ClassroomAvailability,
    ClassroomEquipment,
)
from app.domain.entities.offering import AcademicOffering, OfferingLine
from app.domain.entities.personnel import (
    Instructor,
    InstructorAvailability,
    InstructorContract,
    InstructorSpecialty,
)
from app.domain.entities.scheduling import Group, ScheduleType

__all__ = [
    "InstructorValidationData",
    "SubjectValidationData",
    "ClassroomValidationData",
    "OfferingValidationData",
    "CapacityValidationData",
    "CurriculumValidationData",
]


@dataclass
class InstructorValidationData:
    """All entities required by :class:`InstructorDataValidator`."""

    instructors: list[Instructor] = field(default_factory=list)
    specialties: list[InstructorSpecialty] = field(default_factory=list)
    contracts: list[InstructorContract] = field(default_factory=list)
    availabilities: list[InstructorAvailability] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)


@dataclass
class SubjectValidationData:
    """All entities required by :class:`SubjectDataValidator`."""

    subjects: list[Subject] = field(default_factory=list)
    specialties: list[InstructorSpecialty] = field(default_factory=list)
    offering_lines: list[OfferingLine] = field(default_factory=list)
    classrooms: list[Classroom] = field(default_factory=list)
    classroom_equipment: list[ClassroomEquipment] = field(default_factory=list)
    prerequisites: list[SubjectPrerequisite] = field(default_factory=list)


@dataclass
class ClassroomValidationData:
    """All entities required by :class:`ClassroomDataValidator`."""

    classrooms: list[Classroom] = field(default_factory=list)
    classroom_availabilities: list[ClassroomAvailability] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)


@dataclass
class OfferingValidationData:
    """All entities required by :class:`OfferingDataValidator`."""

    offerings: list[AcademicOffering] = field(default_factory=list)
    offering_lines: list[OfferingLine] = field(default_factory=list)
    subjects: list[Subject] = field(default_factory=list)
    schedule_types: list[ScheduleType] = field(default_factory=list)


@dataclass
class CapacityValidationData:
    """All entities required by :class:`CapacityValidator`."""

    instructors: list[Instructor] = field(default_factory=list)
    contracts: list[InstructorContract] = field(default_factory=list)
    availabilities: list[InstructorAvailability] = field(default_factory=list)
    classrooms: list[Classroom] = field(default_factory=list)
    classroom_availabilities: list[ClassroomAvailability] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)
    offering_lines: list[OfferingLine] = field(default_factory=list)
    subjects: list[Subject] = field(default_factory=list)


@dataclass
class CurriculumValidationData:
    """All entities required by :class:`CurriculumValidator`."""

    plan_subjects: list[PlanSubject] = field(default_factory=list)
    subjects: list[Subject] = field(default_factory=list)
