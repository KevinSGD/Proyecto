"""Abstract repository interfaces for domain entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from app.core.utils.types import EntityId

if TYPE_CHECKING:
    from app.domain.entities.academic import (
        AcademicArea,
        Department,
        PlanSubject,
        Program,
        StudyPlan,
        Subject,
    )
    from app.domain.entities.auth import Permission, Role, User, UserArea
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
        Equipment,
    )
    from app.domain.entities.institution import (
        AcademicPeriod,
        Campus,
        Institution,
    )
    from app.domain.entities.offering import AcademicOffering, OfferingLine
    from app.domain.entities.personnel import (
        Instructor,
        InstructorAvailability,
        InstructorContract,
        InstructorPreference,
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
    from app.domain.entities.system import (
        AuditLog,
        Notification,
        SystemParameter,
    )

T = TypeVar("T")

__all__ = [
    "Repository",
    "InstitutionRepository",
    "CampusRepository",
    "AcademicPeriodRepository",
    "AcademicAreaRepository",
    "DepartmentRepository",
    "SubjectRepository",
    "StudyPlanRepository",
    "PlanSubjectRepository",
    "InstructorRepository",
    "AvailabilityRepository",
    "ContractRepository",
    "PreferenceRepository",
    "SpecialtyRepository",
    "ClassroomRepository",
    "ClassroomAvailabilityRepository",
    "BuildingRepository",
    "EquipmentRepository",
    "OfferingRepository",
    "OfferingLineRepository",
    "GroupRepository",
    "ScheduleTypeRepository",
    "ScheduleRunRepository",
    "AssignmentRepository",
    "SessionBlockRepository",
    "OptimizationConfigRepository",
    "UserRepository",
    "RoleRepository",
    "ImportSessionRepository",
    "ImportTemplateRepository",
    "ValidationReportRepository",
    "AuditLogRepository",
    "SystemParameterRepository",
    "NotificationRepository",
]


# ── generic base ──────────────────────────────────────────────────────────────


class Repository(ABC, Generic[T]):
    """Base repository interface for CRUD operations."""

    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> T | None: ...

    @abstractmethod
    def list_all(self) -> list[T]: ...

    @abstractmethod
    def save(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, entity_id: EntityId) -> bool: ...


# ── institution ───────────────────────────────────────────────────────────────


class InstitutionRepository(Repository["Institution"]):
    @abstractmethod
    def get_by_abbreviation(self, abbreviation: str) -> "Institution | None": ...


class CampusRepository(Repository["Campus"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[Campus]": ...


class AcademicPeriodRepository(Repository["AcademicPeriod"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[AcademicPeriod]": ...

    @abstractmethod
    def get_active(self, institution_id: EntityId) -> "AcademicPeriod | None": ...


# ── academic ──────────────────────────────────────────────────────────────────


class AcademicAreaRepository(Repository["AcademicArea"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[AcademicArea]": ...


class DepartmentRepository(Repository["Department"]):
    @abstractmethod
    def list_by_area(self, area_id: EntityId) -> "list[Department]": ...


class SubjectRepository(Repository["Subject"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[Subject]": ...

    @abstractmethod
    def list_by_study_plan(self, study_plan_id: EntityId) -> "list[Subject]": ...


class StudyPlanRepository(Repository["StudyPlan"]):
    @abstractmethod
    def list_by_program(self, program_id: EntityId) -> "list[StudyPlan]": ...

    @abstractmethod
    def get_active(self, program_id: EntityId) -> "StudyPlan | None": ...


class PlanSubjectRepository(Repository["PlanSubject"]):
    @abstractmethod
    def list_by_study_plan(self, study_plan_id: EntityId) -> "list[PlanSubject]": ...

    @abstractmethod
    def list_by_semester(
        self, study_plan_id: EntityId, semester: int,
    ) -> "list[PlanSubject]": ...


# ── personnel ─────────────────────────────────────────────────────────────────


class InstructorRepository(Repository["Instructor"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[Instructor]": ...

    @abstractmethod
    def list_by_subject(self, subject_id: EntityId) -> "list[Instructor]": ...

    @abstractmethod
    def list_by_department(self, department_id: EntityId) -> "list[Instructor]": ...


class AvailabilityRepository(Repository["InstructorAvailability"]):
    @abstractmethod
    def list_by_instructor(
        self, instructor_id: EntityId, period_id: EntityId | None = None,
    ) -> "list[InstructorAvailability]": ...

    @abstractmethod
    def bulk_save(self, entries: "list[InstructorAvailability]") -> int: ...


class ContractRepository(Repository["InstructorContract"]):
    @abstractmethod
    def get_active(self, instructor_id: EntityId) -> "InstructorContract | None": ...


class PreferenceRepository(Repository["InstructorPreference"]):
    @abstractmethod
    def list_by_instructor(
        self, instructor_id: EntityId, period_id: EntityId | None = None,
    ) -> "list[InstructorPreference]": ...


class SpecialtyRepository(Repository["InstructorSpecialty"]):
    @abstractmethod
    def list_by_instructor(self, instructor_id: EntityId) -> "list[InstructorSpecialty]": ...

    @abstractmethod
    def list_by_subject(self, subject_id: EntityId) -> "list[InstructorSpecialty]": ...


# ── infrastructure ────────────────────────────────────────────────────────────


class BuildingRepository(Repository["Building"]):
    @abstractmethod
    def list_by_campus(self, campus_id: EntityId) -> "list[Building]": ...


class ClassroomRepository(Repository["Classroom"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[Classroom]": ...

    @abstractmethod
    def list_by_min_capacity(
        self, institution_id: EntityId, min_capacity: int,
    ) -> "list[Classroom]": ...

    @abstractmethod
    def list_by_building(self, building_id: EntityId) -> "list[Classroom]": ...


class ClassroomAvailabilityRepository(Repository["ClassroomAvailability"]):
    @abstractmethod
    def list_by_classroom(
        self, classroom_id: EntityId, period_id: EntityId | None = None,
    ) -> "list[ClassroomAvailability]": ...

    @abstractmethod
    def bulk_save(self, entries: "list[ClassroomAvailability]") -> int: ...


class EquipmentRepository(Repository["Equipment"]):
    @abstractmethod
    def list_by_classroom(self, classroom_id: EntityId) -> "list[Equipment]": ...

    @abstractmethod
    def list_required_by_subject(self, subject_id: EntityId) -> "list[Equipment]": ...


# ── offering & scheduling ────────────────────────────────────────────────────


class OfferingRepository(Repository["AcademicOffering"]):
    @abstractmethod
    def list_by_period(
        self, institution_id: EntityId, period_id: EntityId,
    ) -> "list[AcademicOffering]": ...


class OfferingLineRepository(Repository["OfferingLine"]):
    @abstractmethod
    def list_by_offering(self, offering_id: EntityId) -> "list[OfferingLine]": ...


class GroupRepository(Repository["Group"]):
    @abstractmethod
    def list_by_offering(self, offering_id: EntityId) -> "list[Group]": ...

    @abstractmethod
    def list_by_period(
        self, institution_id: EntityId, period_id: EntityId,
    ) -> "list[Group]": ...


class ScheduleTypeRepository(Repository["ScheduleType"]):
    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[ScheduleType]": ...


# ── schedule results ──────────────────────────────────────────────────────────


class ScheduleRunRepository(Repository["ScheduleRun"]):
    @abstractmethod
    def list_by_period(
        self, institution_id: EntityId, period_id: EntityId,
    ) -> "list[ScheduleRun]": ...


class AssignmentRepository(Repository["Assignment"]):
    @abstractmethod
    def list_by_schedule_run(self, run_id: EntityId) -> "list[Assignment]": ...


class SessionBlockRepository(Repository["SessionBlock"]):
    @abstractmethod
    def list_by_assignment(self, assignment_id: EntityId) -> "list[SessionBlock]": ...

    @abstractmethod
    def list_by_schedule_run(self, run_id: EntityId) -> "list[SessionBlock]": ...


class OptimizationConfigRepository(Repository["OptimizationConfig"]):
    @abstractmethod
    def get_default(self, institution_id: EntityId) -> "OptimizationConfig | None": ...

    @abstractmethod
    def list_by_institution(
        self, institution_id: EntityId,
    ) -> "list[OptimizationConfig]": ...


# ── auth ──────────────────────────────────────────────────────────────────────


class UserRepository(Repository["User"]):
    @abstractmethod
    def get_by_email(self, email: str) -> "User | None": ...

    @abstractmethod
    def list_by_institution(self, institution_id: EntityId) -> "list[User]": ...


class RoleRepository(Repository["Role"]):
    @abstractmethod
    def get_by_name(
        self, name: str, institution_id: EntityId | None = None,
    ) -> "Role | None": ...

    @abstractmethod
    def list_permissions(self, role_id: EntityId) -> "list[Permission]": ...


# ── import/export & audit ─────────────────────────────────────────────────────


class ImportSessionRepository(Repository["ImportSession"]):
    @abstractmethod
    def list_by_institution(
        self, institution_id: EntityId,
    ) -> "list[ImportSession]": ...

    @abstractmethod
    def list_entries(
        self, session_id: EntityId,
    ) -> "list[ImportLogEntry]": ...


class ImportTemplateRepository(Repository["ImportTemplate"]):
    @abstractmethod
    def get_active(
        self, institution_id: EntityId | None, entity_type: str,
    ) -> "ImportTemplate | None": ...


class ValidationReportRepository(Repository["ValidationReport"]):
    @abstractmethod
    def list_by_period(
        self, institution_id: EntityId, period_id: EntityId,
    ) -> "list[ValidationReport]": ...


class AuditLogRepository(Repository["AuditLog"]):
    @abstractmethod
    def list_by_entity(
        self, entity_type: str, entity_id: EntityId,
    ) -> "list[AuditLog]": ...

    @abstractmethod
    def list_by_user(self, user_id: EntityId) -> "list[AuditLog]": ...


class SystemParameterRepository(Repository["SystemParameter"]):
    @abstractmethod
    def get_by_key(
        self, key: str, institution_id: EntityId | None = None,
    ) -> "SystemParameter | None": ...


class NotificationRepository(Repository["Notification"]):
    @abstractmethod
    def list_unread(self, user_id: EntityId) -> "list[Notification]": ...

    @abstractmethod
    def mark_read(self, notification_id: EntityId) -> bool: ...
