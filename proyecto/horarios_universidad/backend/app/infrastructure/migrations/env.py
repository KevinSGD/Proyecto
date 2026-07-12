"""Alembic environment configuration for autogenerate support."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infrastructure.persistence.database import Base

# Importing all models ensures they register on Base.metadata before
# Alembic inspects it for autogenerate diffs.
from app.infrastructure.persistence.models import (  # noqa: F401
    AcademicAreaModel,
    AcademicOfferingModel,
    AcademicPeriodModel,
    AssignmentModel,
    AuditLogModel,
    BuildingModel,
    CampusModel,
    ClassroomAvailabilityModel,
    ClassroomModel,
    ExecutionLogModel,
    GroupModel,
    ImportLogEntryModel,
    ImportSessionModel,
    ImportTemplateModel,
    InstitutionModel,
    InstructorAvailabilityModel,
    InstructorContractModel,
    InstructorModel,
    InstructorPreferenceModel,
    InstructorQualificationModel,
    InstructorSpecialtyModel,
    NotificationModel,
    OfferingLineModel,
    OptimizationConfigModel,
    PermissionModel,
    ResourceModel,
    RoleModel,
    RoomResourceModel,
    ScheduleRunModel,
    ScheduleTypeModel,
    SessionBlockModel,
    SubjectModel,
    SubjectResourceRequirementModel,
    SystemParameterModel,
    UserAreaModel,
    UserModel,
    ValidationReportModel,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

database_url = os.environ.get("SCHEDULER_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def _is_sqlite() -> bool:
    url = config.get_main_option("sqlalchemy.url") or ""
    return url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Generate SQL scripts without a live database connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_is_sqlite(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=_is_sqlite(),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
