"""Write-side use cases for schedule generation and management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.application.exceptions.application_exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
)

if TYPE_CHECKING:
    from app.api.schemas.schedule import ScheduleGenerateRequest
    from app.domain.entities.import_export import ValidationReport
    from app.domain.entities.schedule import ScheduleRun
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = [
    "GenerateSchedule",
    "ValidateScheduleData",
    "PublishSchedule",
    "BlockSchedule",
]


class GenerateSchedule:
    """Trigger a full schedule generation pipeline."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, data: ScheduleGenerateRequest) -> ScheduleRun:
        from app.api.config.settings import get_settings
        from app.application.services.schedule_service import (
            ScheduleGenerationService,
        )
        from app.solver.config import SolverConfiguration

        settings = get_settings()
        solver_config = SolverConfiguration(
            max_time_seconds=data.max_time_seconds or settings.solver_max_time_seconds,
            num_workers=data.num_workers or settings.solver_num_workers,
        )

        return ScheduleGenerationService(self._uow).generate(
            institution_id=data.institution_id,
            period_id=data.period_id,
            config=solver_config,
            created_by=data.created_by,
        )


class ValidateScheduleData:
    """Run domain validation before solver execution."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        institution_id,
        period_id,
    ) -> ValidationReport:
        from app.application.services.schedule_service import (
            ScheduleGenerationService,
        )

        return ScheduleGenerationService(self._uow).validate(
            institution_id, period_id,
        )


class PublishSchedule:
    """Mark a completed schedule run as published."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, run_id) -> ScheduleRun:
        with self._uow:
            run = self._uow.schedule_runs.get_by_id(run_id)
            if run is None:
                raise ResourceNotFoundError("ScheduleRun", run_id)
            if run.status not in ("optimal", "feasible"):
                raise BusinessRuleError(
                    f"Cannot publish a run with status '{run.status}'. "
                    "Only 'optimal' or 'feasible' runs can be published.",
                )
            run.status = "published"
            self._uow.schedule_runs.save(run)
            self._uow.commit()
            return run


class BlockSchedule:
    """Mark a schedule run as blocked (prevents further use)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, run_id) -> ScheduleRun:
        with self._uow:
            run = self._uow.schedule_runs.get_by_id(run_id)
            if run is None:
                raise ResourceNotFoundError("ScheduleRun", run_id)
            if run.status == "blocked":
                raise BusinessRuleError("Schedule run is already blocked.")
            run.status = "blocked"
            self._uow.schedule_runs.save(run)
            self._uow.commit()
            return run
