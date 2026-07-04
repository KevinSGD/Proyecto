"""Concrete repositories for system, import/export, and audit aggregates."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

from app.core.utils.types import EntityId
from app.domain.entities.import_export import (
    ImportLogEntry,
    ImportSession,
    ImportTemplate,
    ValidationReport,
)
from app.domain.entities.system import AuditLog, Notification, SystemParameter
from app.domain.interfaces.repositories import (
    AuditLogRepository,
    ImportSessionRepository,
    ImportTemplateRepository,
    NotificationRepository,
    SystemParameterRepository,
    ValidationReportRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ── import / export ──────────────────────────────────────────────────────────


class SqlImportSessionRepository(
    SqlAlchemyRepository[ImportSession],
    ImportSessionRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.import_export import (
            ImportSessionModel,
        )

        self._model_cls = ImportSessionModel
        self._entity_cls = ImportSession
        super().__init__(session)

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[ImportSession]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_entries(
        self, session_id: EntityId,
    ) -> list[ImportLogEntry]:
        from app.infrastructure.persistence.models.import_export import (
            ImportLogEntryModel,
        )

        models = (
            self._session.query(ImportLogEntryModel)
            .filter(ImportLogEntryModel.import_session_id == session_id)
            .all()
        )
        return [self._log_entry_to_entity(m) for m in models]

    @staticmethod
    def _log_entry_to_entity(model: Any) -> ImportLogEntry:
        fields = dataclasses.fields(ImportLogEntry)
        kwargs: dict[str, Any] = {}
        for f in fields:
            if hasattr(model, f.name):
                kwargs[f.name] = getattr(model, f.name)
        return ImportLogEntry(**kwargs)


class SqlImportTemplateRepository(
    SqlAlchemyRepository[ImportTemplate],
    ImportTemplateRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.import_export import (
            ImportTemplateModel,
        )

        self._model_cls = ImportTemplateModel
        self._entity_cls = ImportTemplate
        super().__init__(session)

    def get_active(
        self,
        institution_id: EntityId | None,
        entity_type: str,
    ) -> ImportTemplate | None:
        query = self._query().filter(
            self._model_cls.entity_type == entity_type,
            self._model_cls.is_active.is_(True),
        )
        if institution_id is not None:
            query = query.filter(
                self._model_cls.institution_id == institution_id,
            )
        else:
            query = query.filter(self._model_cls.institution_id.is_(None))
        model = query.first()
        return self._to_entity(model) if model else None


class SqlValidationReportRepository(
    SqlAlchemyRepository[ValidationReport],
    ValidationReportRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.import_export import (
            ValidationReportModel,
        )

        self._model_cls = ValidationReportModel
        self._entity_cls = ValidationReport
        super().__init__(session)

    def list_by_period(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> list[ValidationReport]:
        models = (
            self._query()
            .filter(
                self._model_cls.institution_id == institution_id,
                self._model_cls.period_id == period_id,
            )
            .all()
        )
        return [self._to_entity(m) for m in models]


# ── audit & system ───────────────────────────────────────────────────────────


class SqlAuditLogRepository(
    SqlAlchemyRepository[AuditLog],
    AuditLogRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.system import AuditLogModel

        self._model_cls = AuditLogModel
        self._entity_cls = AuditLog
        super().__init__(session)

    def list_by_entity(
        self,
        entity_type: str,
        entity_id: EntityId,
    ) -> list[AuditLog]:
        models = (
            self._query()
            .filter(
                self._model_cls.entity_type == entity_type,
                self._model_cls.entity_id == entity_id,
            )
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_user(self, user_id: EntityId) -> list[AuditLog]:
        models = (
            self._query()
            .filter(self._model_cls.user_id == user_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlSystemParameterRepository(
    SqlAlchemyRepository[SystemParameter],
    SystemParameterRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.system import (
            SystemParameterModel,
        )

        self._model_cls = SystemParameterModel
        self._entity_cls = SystemParameter
        super().__init__(session)

    def get_by_key(
        self,
        key: str,
        institution_id: EntityId | None = None,
    ) -> SystemParameter | None:
        query = self._query().filter(self._model_cls.key == key)
        if institution_id is not None:
            query = query.filter(
                self._model_cls.institution_id == institution_id,
            )
        else:
            query = query.filter(self._model_cls.institution_id.is_(None))
        model = query.first()
        return self._to_entity(model) if model else None


class SqlNotificationRepository(
    SqlAlchemyRepository[Notification],
    NotificationRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.system import (
            NotificationModel,
        )

        self._model_cls = NotificationModel
        self._entity_cls = Notification
        super().__init__(session)

    def list_unread(self, user_id: EntityId) -> list[Notification]:
        models = (
            self._query()
            .filter(
                self._model_cls.user_id == user_id,
                self._model_cls.is_read.is_(False),
            )
            .all()
        )
        return [self._to_entity(m) for m in models]

    def mark_read(self, notification_id: EntityId) -> bool:
        model = self._session.get(self._model_cls, notification_id)
        if model is None:
            return False
        model.is_read = True  # type: ignore[attr-defined]
        self._session.flush()
        return True
