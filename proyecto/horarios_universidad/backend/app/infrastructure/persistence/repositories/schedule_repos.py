"""Concrete repositories for schedule result aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils.types import EntityId
from app.domain.entities.schedule import (
    Assignment,
    ExecutionLog,
    OptimizationConfig,
    ScheduleRun,
    SessionBlock,
)
from app.domain.interfaces.repositories import (
    AssignmentRepository,
    ExecutionLogRepository,
    OptimizationConfigRepository,
    ScheduleRunRepository,
    SessionBlockRepository,
)
from app.infrastructure.persistence.repositories.base import SqlAlchemyRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SqlScheduleRunRepository(
    SqlAlchemyRepository[ScheduleRun],
    ScheduleRunRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.schedule import (
            ScheduleRunModel,
        )

        self._model_cls = ScheduleRunModel
        self._entity_cls = ScheduleRun
        super().__init__(session)

    def list_by_period(
        self,
        institution_id: EntityId,
        period_id: EntityId,
    ) -> list[ScheduleRun]:
        models = (
            self._query()
            .filter(
                self._model_cls.institution_id == institution_id,
                self._model_cls.period_id == period_id,
            )
            .order_by(self._model_cls.started_at.desc())
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlAssignmentRepository(
    SqlAlchemyRepository[Assignment],
    AssignmentRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.schedule import (
            AssignmentModel,
        )

        self._model_cls = AssignmentModel
        self._entity_cls = Assignment
        super().__init__(session)

    def list_by_schedule_run(
        self, run_id: EntityId,
    ) -> list[Assignment]:
        models = (
            self._query()
            .filter(self._model_cls.schedule_run_id == run_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlSessionBlockRepository(
    SqlAlchemyRepository[SessionBlock],
    SessionBlockRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.schedule import (
            SessionBlockModel,
        )

        self._model_cls = SessionBlockModel
        self._entity_cls = SessionBlock
        super().__init__(session)

    def list_by_assignment(
        self, assignment_id: EntityId,
    ) -> list[SessionBlock]:
        models = (
            self._query()
            .filter(self._model_cls.assignment_id == assignment_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def list_by_schedule_run(
        self, run_id: EntityId,
    ) -> list[SessionBlock]:
        from app.infrastructure.persistence.models.schedule import (
            AssignmentModel,
        )

        assignment_ids = (
            self._session.query(AssignmentModel.id)
            .filter(AssignmentModel.schedule_run_id == run_id)
            .subquery()
        )
        models = (
            self._query()
            .filter(self._model_cls.assignment_id.in_(assignment_ids))
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlOptimizationConfigRepository(
    SqlAlchemyRepository[OptimizationConfig],
    OptimizationConfigRepository,
):
    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.schedule import (
            OptimizationConfigModel,
        )

        self._model_cls = OptimizationConfigModel
        self._entity_cls = OptimizationConfig
        super().__init__(session)

    def get_default(
        self, institution_id: EntityId,
    ) -> OptimizationConfig | None:
        model = (
            self._query()
            .filter(
                self._model_cls.institution_id == institution_id,
                self._model_cls.is_default.is_(True),
            )
            .first()
        )
        return self._to_entity(model) if model else None

    def list_by_institution(
        self, institution_id: EntityId,
    ) -> list[OptimizationConfig]:
        models = (
            self._query()
            .filter(self._model_cls.institution_id == institution_id)
            .all()
        )
        return [self._to_entity(m) for m in models]


class SqlExecutionLogRepository(
    SqlAlchemyRepository[ExecutionLog],
    ExecutionLogRepository,
):
    """Persists solver execution event logs."""

    def __init__(self, session: Session) -> None:
        from app.infrastructure.persistence.models.schedule import (
            ExecutionLogModel,
        )

        self._model_cls = ExecutionLogModel
        self._entity_cls = ExecutionLog
        super().__init__(session)

    def list_by_run(
        self, schedule_run_id: EntityId,
    ) -> list[ExecutionLog]:
        models = (
            self._query()
            .filter(self._model_cls.schedule_run_id == schedule_run_id)
            .order_by(self._model_cls.timestamp)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: object) -> ExecutionLog:
        return ExecutionLog(
            id=model.id,  # type: ignore[attr-defined]
            schedule_run_id=model.schedule_run_id,  # type: ignore[attr-defined]
            event_type=model.event_type,  # type: ignore[attr-defined]
            message=model.message,  # type: ignore[attr-defined]
            timestamp=model.timestamp,  # type: ignore[attr-defined]
            metadata=model.metadata_,  # type: ignore[attr-defined]
        )

    def _to_model(self, entity: ExecutionLog) -> object:
        from app.infrastructure.persistence.models.schedule import (
            ExecutionLogModel,
        )

        return ExecutionLogModel(
            id=entity.id,
            schedule_run_id=entity.schedule_run_id,
            event_type=entity.event_type,
            message=entity.message,
            timestamp=entity.timestamp,
            metadata_=entity.metadata,
        )
