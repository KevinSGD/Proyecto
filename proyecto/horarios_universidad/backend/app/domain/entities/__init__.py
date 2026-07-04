"""Domain entity re-exports."""

from app.domain.entities.academic import (
    AcademicArea,
    Department,
    PlanSubject,
    Program,
    StudyPlan,
    Subject,
    SubjectPrerequisite,
)
from app.domain.entities.auth import Permission, Role, RoleName, User, UserArea
from app.domain.entities.import_export import (
    ImportLogEntry,
    ImportSession,
    ImportTemplate,
    ValidationReport,
)
from app.domain.entities.infrastructure import (
    Building,
    Classroom,
    ClassroomAvailability,
    ClassroomEquipment,
    ClassroomType,
    Equipment,
    SubjectEquipmentRequirement,
)
from app.domain.entities.institution import AcademicPeriod, Campus, Institution
from app.domain.entities.offering import AcademicOffering, OfferingLine
from app.domain.entities.personnel import (
    Instructor,
    InstructorAvailability,
    InstructorContract,
    InstructorPreference,
    InstructorQualification,
    InstructorSpecialty,
)
from app.domain.entities.schedule import (
    Assignment,
    ExecutionLog,
    OptimizationConfig,
    ScheduleRun,
    SessionBlock,
)
from app.domain.entities.scheduling import Group, ScheduleType
from app.domain.entities.system import AuditLog, Notification, SystemParameter

__all__ = [
    # institution
    "Institution",
    "Campus",
    "AcademicPeriod",
    # academic
    "AcademicArea",
    "Department",
    "Program",
    "StudyPlan",
    "PlanSubject",
    "Subject",
    "SubjectPrerequisite",
    # personnel
    "Instructor",
    "InstructorContract",
    "InstructorSpecialty",
    "InstructorQualification",
    "InstructorAvailability",
    "InstructorPreference",
    # infrastructure
    "Building",
    "ClassroomType",
    "Classroom",
    "ClassroomAvailability",
    "Equipment",
    "ClassroomEquipment",
    "SubjectEquipmentRequirement",
    # offering
    "AcademicOffering",
    "OfferingLine",
    # scheduling
    "ScheduleType",
    "Group",
    # schedule
    "OptimizationConfig",
    "ScheduleRun",
    "Assignment",
    "SessionBlock",
    "ExecutionLog",
    # auth
    "RoleName",
    "Role",
    "Permission",
    "User",
    "UserArea",
    # system
    "AuditLog",
    "SystemParameter",
    "Notification",
    # import/export
    "ImportSession",
    "ImportLogEntry",
    "ImportTemplate",
    "ValidationReport",
]
