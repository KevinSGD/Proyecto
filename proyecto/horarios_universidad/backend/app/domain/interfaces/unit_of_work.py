"""Unit of Work abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.interfaces.repositories import (
        AssignmentRepository,
        AuditLogRepository,
        AvailabilityRepository,
        BuildingRepository,
        CampusRepository,
        ClassroomAvailabilityRepository,
        ClassroomRepository,
        ContractRepository,
        DepartmentRepository,
        EquipmentRepository,
        GroupRepository,
        ImportSessionRepository,
        InstitutionRepository,
        InstructorRepository,
        NotificationRepository,
        OfferingLineRepository,
        OfferingRepository,
        OptimizationConfigRepository,
        PlanSubjectRepository,
        PreferenceRepository,
        RoleRepository,
        ScheduleRunRepository,
        ScheduleTypeRepository,
        SessionBlockRepository,
        SpecialtyRepository,
        StudyPlanRepository,
        SubjectRepository,
        SystemParameterRepository,
        UserRepository,
        ValidationReportRepository,
    )

__all__ = ["UnitOfWork"]


class UnitOfWork(ABC):
    """Transactional boundary across multiple repositories."""

    @abstractmethod
    def __enter__(self) -> UnitOfWork: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    # ── repository accessors ──────────────────────────────────────────

    @property
    @abstractmethod
    def institutions(self) -> InstitutionRepository: ...

    @property
    @abstractmethod
    def campuses(self) -> CampusRepository: ...

    @property
    @abstractmethod
    def departments(self) -> DepartmentRepository: ...

    @property
    @abstractmethod
    def subjects(self) -> SubjectRepository: ...

    @property
    @abstractmethod
    def study_plans(self) -> StudyPlanRepository: ...

    @property
    @abstractmethod
    def plan_subjects(self) -> PlanSubjectRepository: ...

    @property
    @abstractmethod
    def instructors(self) -> InstructorRepository: ...

    @property
    @abstractmethod
    def availabilities(self) -> AvailabilityRepository: ...

    @property
    @abstractmethod
    def contracts(self) -> ContractRepository: ...

    @property
    @abstractmethod
    def preferences(self) -> PreferenceRepository: ...

    @property
    @abstractmethod
    def specialties(self) -> SpecialtyRepository: ...

    @property
    @abstractmethod
    def buildings(self) -> BuildingRepository: ...

    @property
    @abstractmethod
    def classrooms(self) -> ClassroomRepository: ...

    @property
    @abstractmethod
    def classroom_availabilities(self) -> ClassroomAvailabilityRepository: ...

    @property
    @abstractmethod
    def equipment(self) -> EquipmentRepository: ...

    @property
    @abstractmethod
    def offerings(self) -> OfferingRepository: ...

    @property
    @abstractmethod
    def offering_lines(self) -> OfferingLineRepository: ...

    @property
    @abstractmethod
    def groups(self) -> GroupRepository: ...

    @property
    @abstractmethod
    def schedule_types(self) -> ScheduleTypeRepository: ...

    @property
    @abstractmethod
    def schedule_runs(self) -> ScheduleRunRepository: ...

    @property
    @abstractmethod
    def assignments(self) -> AssignmentRepository: ...

    @property
    @abstractmethod
    def session_blocks(self) -> SessionBlockRepository: ...

    @property
    @abstractmethod
    def optimization_configs(self) -> OptimizationConfigRepository: ...

    @property
    @abstractmethod
    def users(self) -> UserRepository: ...

    @property
    @abstractmethod
    def roles(self) -> RoleRepository: ...

    @property
    @abstractmethod
    def import_sessions(self) -> ImportSessionRepository: ...

    @property
    @abstractmethod
    def validation_reports(self) -> ValidationReportRepository: ...

    @property
    @abstractmethod
    def audit_logs(self) -> AuditLogRepository: ...

    @property
    @abstractmethod
    def system_parameters(self) -> SystemParameterRepository: ...

    @property
    @abstractmethod
    def notifications(self) -> NotificationRepository: ...
