"""Concrete SQLAlchemy repository implementations."""

from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository
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
from app.infrastructure.persistence.repositories.institution_repos import (
    SqlAcademicPeriodRepository,
    SqlCampusRepository,
    SqlInstitutionRepository,
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
from app.infrastructure.persistence.repositories.system_repos import (
    SqlAuditLogRepository,
    SqlImportSessionRepository,
    SqlImportTemplateRepository,
    SqlNotificationRepository,
    SqlSystemParameterRepository,
    SqlValidationReportRepository,
)

__all__ = [
    "SqlAlchemyRepository",
    # institution
    "SqlInstitutionRepository",
    "SqlCampusRepository",
    "SqlAcademicPeriodRepository",
    # academic
    "SqlAcademicAreaRepository",
    "SqlSubjectRepository",
    # personnel
    "SqlInstructorRepository",
    "SqlAvailabilityRepository",
    "SqlContractRepository",
    "SqlPreferenceRepository",
    "SqlSpecialtyRepository",
    # infrastructure
    "SqlBuildingRepository",
    "SqlClassroomRepository",
    "SqlClassroomAvailabilityRepository",
    "SqlResourceRepository",
    # offering & scheduling
    "SqlOfferingRepository",
    "SqlOfferingLineRepository",
    "SqlGroupRepository",
    "SqlScheduleTypeRepository",
    # schedule results
    "SqlScheduleRunRepository",
    "SqlAssignmentRepository",
    "SqlSessionBlockRepository",
    "SqlExecutionLogRepository",
    "SqlOptimizationConfigRepository",
    # auth
    "SqlUserRepository",
    "SqlUserAreaRepository",
    "SqlRoleRepository",
    # system & import/export
    "SqlImportSessionRepository",
    "SqlImportTemplateRepository",
    "SqlValidationReportRepository",
    "SqlAuditLogRepository",
    "SqlSystemParameterRepository",
    "SqlNotificationRepository",
]
