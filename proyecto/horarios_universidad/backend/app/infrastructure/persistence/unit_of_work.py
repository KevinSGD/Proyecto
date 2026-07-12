"""SQLAlchemy-backed Unit of Work implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.persistence.repositories.academic_repos import (
    SqlAcademicAreaRepository,
    SqlSubjectRepository,
)
from app.infrastructure.persistence.repositories.auth_repos import (
    SqlRoleRepository,
    SqlUserAreaRepository,
    SqlUserRepository,
)
from app.infrastructure.persistence.repositories.infrastructure_repos import (
    SqlBuildingRepository,
    SqlClassroomAvailabilityRepository,
    SqlClassroomRepository,
    SqlResourceRepository,
)
from app.infrastructure.persistence.repositories.offering_repos import (
    SqlGroupRepository,
    SqlOfferingLineRepository,
    SqlOfferingRepository,
    SqlScheduleTypeRepository,
)
from app.infrastructure.persistence.repositories.personnel_repos import (
    SqlAvailabilityRepository,
    SqlContractRepository,
    SqlInstructorRepository,
    SqlPreferenceRepository,
    SqlSpecialtyRepository,
)
from app.infrastructure.persistence.repositories.schedule_repos import (
    SqlAssignmentRepository,
    SqlExecutionLogRepository,
    SqlOptimizationConfigRepository,
    SqlScheduleRunRepository,
    SqlSessionBlockRepository,
)
from app.infrastructure.persistence.repositories.institution_repos import (
    SqlAcademicPeriodRepository,
    SqlCampusRepository,
    SqlInstitutionRepository,
)
from app.infrastructure.persistence.repositories.system_repos import (
    SqlAuditLogRepository,
    SqlImportSessionRepository,
    SqlNotificationRepository,
    SqlSystemParameterRepository,
    SqlValidationReportRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

    from app.domain.interfaces.repositories import (
        AcademicAreaRepository,
        AcademicPeriodRepository,
        AssignmentRepository,
        AuditLogRepository,
        AvailabilityRepository,
        BuildingRepository,
        CampusRepository,
        ClassroomAvailabilityRepository,
        ClassroomRepository,
        ContractRepository,
        ResourceRepository,
        ExecutionLogRepository,
        GroupRepository,
        ImportSessionRepository,
        InstitutionRepository,
        InstructorRepository,
        NotificationRepository,
        OfferingLineRepository,
        OfferingRepository,
        OptimizationConfigRepository,
        PreferenceRepository,
        RoleRepository,
        UserAreaRepository,
        ScheduleRunRepository,
        ScheduleTypeRepository,
        SessionBlockRepository,
        SpecialtyRepository,
        SubjectRepository,
        SystemParameterRepository,
        UserRepository,
        ValidationReportRepository,
    )


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Transactional boundary backed by a SQLAlchemy session."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    # ── context manager ──────────────────────────────────────────────

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self._repos: dict[str, object] = {}
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        self._ensure_session().close()
        self._session = None

    def commit(self) -> None:
        self._ensure_session().commit()

    def rollback(self) -> None:
        self._ensure_session().rollback()

    # ── private helpers ──────────────────────────────────────────────

    def _ensure_session(self) -> Session:
        if self._session is None:
            raise RuntimeError(
                "UnitOfWork must be used inside a with-block",
            )
        return self._session

    def _get_repo(self, key: str, factory: type) -> object:
        if key not in self._repos:
            self._repos[key] = factory(self._ensure_session())
        return self._repos[key]

    # ── repository accessors ─────────────────────────────────────────

    @property
    def institutions(self) -> InstitutionRepository:
        return self._get_repo("institutions", SqlInstitutionRepository)  # type: ignore[return-value]

    @property
    def campuses(self) -> CampusRepository:
        return self._get_repo("campuses", SqlCampusRepository)  # type: ignore[return-value]

    @property
    def academic_periods(self) -> AcademicPeriodRepository:
        return self._get_repo("academic_periods", SqlAcademicPeriodRepository)  # type: ignore[return-value]

    @property
    def academic_areas(self) -> AcademicAreaRepository:
        return self._get_repo("academic_areas", SqlAcademicAreaRepository)  # type: ignore[return-value]

    @property
    def subjects(self) -> SubjectRepository:
        return self._get_repo("subjects", SqlSubjectRepository)  # type: ignore[return-value]

    @property
    def instructors(self) -> InstructorRepository:
        return self._get_repo("instructors", SqlInstructorRepository)  # type: ignore[return-value]

    @property
    def availabilities(self) -> AvailabilityRepository:
        return self._get_repo("availabilities", SqlAvailabilityRepository)  # type: ignore[return-value]

    @property
    def contracts(self) -> ContractRepository:
        return self._get_repo("contracts", SqlContractRepository)  # type: ignore[return-value]

    @property
    def preferences(self) -> PreferenceRepository:
        return self._get_repo("preferences", SqlPreferenceRepository)  # type: ignore[return-value]

    @property
    def specialties(self) -> SpecialtyRepository:
        return self._get_repo("specialties", SqlSpecialtyRepository)  # type: ignore[return-value]

    @property
    def buildings(self) -> BuildingRepository:
        return self._get_repo("buildings", SqlBuildingRepository)  # type: ignore[return-value]

    @property
    def classrooms(self) -> ClassroomRepository:
        return self._get_repo("classrooms", SqlClassroomRepository)  # type: ignore[return-value]

    @property
    def classroom_availabilities(self) -> ClassroomAvailabilityRepository:
        return self._get_repo("classroom_availabilities", SqlClassroomAvailabilityRepository)  # type: ignore[return-value]

    @property
    def resources(self) -> ResourceRepository:
        return self._get_repo("resources", SqlResourceRepository)  # type: ignore[return-value]

    @property
    def offerings(self) -> OfferingRepository:
        return self._get_repo("offerings", SqlOfferingRepository)  # type: ignore[return-value]

    @property
    def offering_lines(self) -> OfferingLineRepository:
        return self._get_repo("offering_lines", SqlOfferingLineRepository)  # type: ignore[return-value]

    @property
    def groups(self) -> GroupRepository:
        return self._get_repo("groups", SqlGroupRepository)  # type: ignore[return-value]

    @property
    def schedule_types(self) -> ScheduleTypeRepository:
        return self._get_repo("schedule_types", SqlScheduleTypeRepository)  # type: ignore[return-value]

    @property
    def schedule_runs(self) -> ScheduleRunRepository:
        return self._get_repo("schedule_runs", SqlScheduleRunRepository)  # type: ignore[return-value]

    @property
    def assignments(self) -> AssignmentRepository:
        return self._get_repo("assignments", SqlAssignmentRepository)  # type: ignore[return-value]

    @property
    def session_blocks(self) -> SessionBlockRepository:
        return self._get_repo("session_blocks", SqlSessionBlockRepository)  # type: ignore[return-value]

    @property
    def execution_logs(self) -> ExecutionLogRepository:
        return self._get_repo("execution_logs", SqlExecutionLogRepository)  # type: ignore[return-value]

    @property
    def optimization_configs(self) -> OptimizationConfigRepository:
        return self._get_repo("optimization_configs", SqlOptimizationConfigRepository)  # type: ignore[return-value]

    @property
    def users(self) -> UserRepository:
        return self._get_repo("users", SqlUserRepository)  # type: ignore[return-value]

    @property
    def roles(self) -> RoleRepository:
        return self._get_repo("roles", SqlRoleRepository)  # type: ignore[return-value]

    @property
    def user_areas(self) -> UserAreaRepository:
        return self._get_repo("user_areas", SqlUserAreaRepository)  # type: ignore[return-value]

    @property
    def import_sessions(self) -> ImportSessionRepository:
        return self._get_repo("import_sessions", SqlImportSessionRepository)  # type: ignore[return-value]

    @property
    def validation_reports(self) -> ValidationReportRepository:
        return self._get_repo("validation_reports", SqlValidationReportRepository)  # type: ignore[return-value]

    @property
    def audit_logs(self) -> AuditLogRepository:
        return self._get_repo("audit_logs", SqlAuditLogRepository)  # type: ignore[return-value]

    @property
    def system_parameters(self) -> SystemParameterRepository:
        return self._get_repo("system_parameters", SqlSystemParameterRepository)  # type: ignore[return-value]

    @property
    def notifications(self) -> NotificationRepository:
        return self._get_repo("notifications", SqlNotificationRepository)  # type: ignore[return-value]
