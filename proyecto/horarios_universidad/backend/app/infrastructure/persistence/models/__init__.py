"""SQLAlchemy ORM models -- re-exports for convenient imports."""

from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.models.academic import (
    AcademicAreaModel,
    SubjectModel,
)
from app.infrastructure.persistence.models.auth import (
    PermissionModel,
    RoleModel,
    UserAreaModel,
    UserModel,
)
from app.infrastructure.persistence.models.import_export import (
    ImportLogEntryModel,
    ImportSessionModel,
    ImportTemplateModel,
    ValidationReportModel,
)
from app.infrastructure.persistence.models.infrastructure_models import (
    BuildingModel,
    ClassroomAvailabilityModel,
    ClassroomModel,
    ResourceModel,
    RoomResourceModel,
    SubjectResourceRequirementModel,
)
from app.infrastructure.persistence.models.institution import (
    AcademicPeriodModel,
    CampusModel,
    InstitutionModel,
)
from app.infrastructure.persistence.models.offering import (
    AcademicOfferingModel,
    OfferingLineModel,
)
from app.infrastructure.persistence.models.personnel import (
    InstructorAvailabilityModel,
    InstructorContractModel,
    InstructorModel,
    InstructorPreferenceModel,
    InstructorQualificationModel,
    InstructorSpecialtyModel,
)
from app.infrastructure.persistence.models.schedule import (
    AssignmentModel,
    ExecutionLogModel,
    OptimizationConfigModel,
    ScheduleRunModel,
    SessionBlockModel,
)
from app.infrastructure.persistence.models.scheduling import (
    GroupModel,
    ScheduleTypeModel,
)
from app.infrastructure.persistence.models.system import (
    AuditLogModel,
    NotificationModel,
    SystemParameterModel,
)

__all__ = [
    "Base",
    "InstitutionModel",
    "CampusModel",
    "AcademicPeriodModel",
    "AcademicAreaModel",
    "SubjectModel",
    "InstructorModel",
    "InstructorContractModel",
    "InstructorSpecialtyModel",
    "InstructorQualificationModel",
    "InstructorAvailabilityModel",
    "InstructorPreferenceModel",
    "BuildingModel",
    "ClassroomModel",
    "ClassroomAvailabilityModel",
    "ResourceModel",
    "RoomResourceModel",
    "SubjectResourceRequirementModel",
    "AcademicOfferingModel",
    "OfferingLineModel",
    "ScheduleTypeModel",
    "GroupModel",
    "OptimizationConfigModel",
    "ScheduleRunModel",
    "AssignmentModel",
    "SessionBlockModel",
    "ExecutionLogModel",
    "RoleModel",
    "PermissionModel",
    "UserModel",
    "UserAreaModel",
    "AuditLogModel",
    "SystemParameterModel",
    "NotificationModel",
    "ImportSessionModel",
    "ImportLogEntryModel",
    "ImportTemplateModel",
    "ValidationReportModel",
]
