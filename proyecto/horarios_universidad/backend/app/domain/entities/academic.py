"""Academic structure entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.utils.types import EntityId, generate_id

__all__ = [
    "AcademicArea",
    "Department",
    "Program",
    "StudyPlan",
    "PlanSubject",
    "Subject",
    "SubjectPrerequisite",
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
class Department:
    """An organizational unit within an academic area."""

    id: EntityId = field(default_factory=generate_id)
    area_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    code: str = ""
    head_instructor_id: EntityId | None = None
    is_active: bool = True


@dataclass
class Program:
    """An academic program (e.g. Computer Science degree)."""

    id: EntityId = field(default_factory=generate_id)
    area_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    code: str = ""
    total_semesters: int = 0
    description: str = ""
    is_active: bool = True


@dataclass
class StudyPlan:
    """A versioned curriculum for a program."""

    id: EntityId = field(default_factory=generate_id)
    program_id: EntityId = field(default_factory=generate_id)
    name: str = ""
    version: str = ""
    year: int = 0
    is_active: bool = True
    total_credits: int = 0


@dataclass
class PlanSubject:
    """Association of a subject to a study plan at a given semester."""

    id: EntityId = field(default_factory=generate_id)
    study_plan_id: EntityId = field(default_factory=generate_id)
    subject_id: EntityId = field(default_factory=generate_id)
    semester: int = 0
    is_elective: bool = False


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
    requires_lab: bool = False
    required_equipment: list[EntityId] = field(default_factory=list)
    is_active: bool = True


@dataclass
class SubjectPrerequisite:
    """Prerequisite relationship between two subjects."""

    id: EntityId = field(default_factory=generate_id)
    subject_id: EntityId = field(default_factory=generate_id)
    prerequisite_subject_id: EntityId = field(default_factory=generate_id)
    prerequisite_type: str = "required"
