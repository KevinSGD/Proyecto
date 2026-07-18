"""Orchestrates the full schedule generation pipeline.

Coordinates DatasetBuilder, SolverEngine, and ResultPublisher to produce
a complete schedule run from raw domain data.  Tracks execution stages
via ExecutionTracker for real-time progress visibility and diagnostics.
"""

from __future__ import annotations

import traceback as tb_module
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.application.services.execution_tracker import (
    ExecutionStage,
    ExecutionTracker,
)
from app.core.logging.logger import get_logger
from app.core.utils.types import EntityId, generate_id
from app.domain.entities.schedule import ScheduleRun

if TYPE_CHECKING:
    from app.domain.entities.import_export import ValidationReport
    from app.domain.interfaces.unit_of_work import UnitOfWork
    from app.solver.config import SolverConfiguration

__all__ = ["ScheduleGenerationService"]

_logger = get_logger(__name__)


class ScheduleGenerationService:
    """Orchestrates the full schedule generation pipeline."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def generate(
        self,
        institution_id: EntityId,
        period_id: EntityId,
        config: SolverConfiguration | None = None,
        created_by: EntityId | None = None,
    ) -> ScheduleRun:
        """Run the end-to-end pipeline synchronously and return the completed run.

        Stages tracked:
        1. Inicializando — create run record, configure solver.
        2. Validando — (reserved for pre-solve domain validation).
        3. Construyendo modelo — DatasetBuilder transforms DB to OptimizationProblem.
        4. Generando variables — (within SolverEngine model build).
        5. Aplicando restricciones — (within SolverEngine constraint application).
        6. Optimizando — CP-SAT solve.
        7. Extrayendo solución — solution extraction.
        8. Guardando — ResultPublisher persists assignments.
        9. Publicado — pipeline complete.
        """
        from app.solver.config import SolverConfiguration as SolverCfg

        solver_config = config or SolverCfg()
        run = self.start(institution_id, period_id, solver_config, created_by)
        return self.run_pipeline(run, solver_config)

    def start(
        self,
        institution_id: EntityId,
        period_id: EntityId,
        config: SolverConfiguration | None = None,
        created_by: EntityId | None = None,
    ) -> ScheduleRun:
        """Create the initial ``running`` ScheduleRun and return immediately.

        Call ``run_pipeline`` afterwards (typically on a background thread)
        to actually execute the solver and populate results.
        """
        from app.solver.config import SolverConfiguration as SolverCfg

        solver_config = config or SolverCfg()
        return self._create_run(
            institution_id, period_id, solver_config, created_by,
        )

    def run_pipeline(
        self,
        run: ScheduleRun,
        config: SolverConfiguration | None = None,
    ) -> ScheduleRun:
        """Execute the solver pipeline for an already-created run.

        Persists execution-log entries at each stage transition so that
        progress can be polled in real time via ``GET /schedule-runs/{id}/logs``.
        """
        from app.solver.config import SolverConfiguration as SolverCfg

        solver_config = config or SolverCfg()
        tracker = ExecutionTracker(self._uow, run.id)

        try:
            tracker.begin(ExecutionStage.INICIALIZANDO)
            tracker.log_event(
                "execution",
                f"Configuración: max_time={solver_config.max_time_seconds}s, "
                f"workers={solver_config.num_workers}",
                metadata={
                    "solver_config": {
                        "max_time_seconds": solver_config.max_time_seconds,
                        "num_workers": solver_config.num_workers,
                        "gap_tolerance": solver_config.gap_tolerance,
                    },
                },
            )

            tracker.advance(ExecutionStage.VALIDANDO)

            tracker.advance(ExecutionStage.CONSTRUYENDO_MODELO)
            from app.application.services.dataset_builder import DatasetBuilder

            problem = DatasetBuilder(self._uow).build(
                run.institution_id, run.period_id,
            )
            tracker.log_event(
                "execution",
                f"Dataset construido: {len(problem.groups)} grupos, "
                f"{len(problem.instructors)} docentes, "
                f"{len(problem.classrooms)} aulas",
                metadata={
                    "groups": len(problem.groups),
                    "instructors": len(problem.instructors),
                    "classrooms": len(problem.classrooms),
                    "time_slots": problem.total_slots,
                },
            )

            tracker.advance(ExecutionStage.OPTIMIZANDO)
            from app.solver.engine import SolverEngine

            result = SolverEngine(solver_config).solve(problem)
            tracker.log_event(
                "solver",
                f"Solver terminó con estado: {result.status.value}",
                metadata={
                    "status": result.status.value,
                    "objective_value": (
                        result.statistics.objective_value
                        if result.statistics else None
                    ),
                    "gap": (
                        result.statistics.gap
                        if result.statistics else None
                    ),
                    "assignments_count": len(result.assignments),
                },
            )

            tracker.advance(ExecutionStage.GUARDANDO)
            from app.application.services.result_publisher import ResultPublisher

            ResultPublisher(self._uow).publish(result, run.id)
            tracker.log_event(
                "persistence",
                f"Resultados guardados: {len(result.assignments)} asignaciones",
            )

            tracker.complete()

            with self._uow:
                updated = self._uow.schedule_runs.get_by_id(run.id)
                if updated is not None:
                    run = updated

        except Exception as exc:
            _logger.exception("Schedule generation failed for run %s", run.id)
            tracker.fail(exc)
            self._mark_error(run.id, exc)
            with self._uow:
                updated = self._uow.schedule_runs.get_by_id(run.id)
                if updated is not None:
                    run = updated

        return run

    def validate(
        self,
        institution_id: EntityId,
        period_id: EntityId,
        run_id: EntityId | None = None,
    ) -> ValidationReport:
        """Run domain validation and return the report."""
        from app.application.services.domain_validator import (
            DomainValidationService,
        )

        return DomainValidationService(self._uow).validate_for_optimization(
            institution_id, period_id, run_id,
        )

    # ── private helpers ──────────────────────────────────────────────────

    def _create_run(
        self,
        institution_id: EntityId,
        period_id: EntityId,
        solver_config: SolverConfiguration,
        created_by: EntityId | None,
    ) -> ScheduleRun:
        """Persist an initial ScheduleRun with status='running'."""
        started_at = datetime.now(timezone.utc)
        with self._uow:
            existing = self._uow.schedule_runs.list_by_period(institution_id, period_id)
            version = len(existing) + 1

        name = f"Corrida v{version} · {started_at.strftime('%H:%M %d/%m/%Y')}"

        run = ScheduleRun(
            id=generate_id(),
            institution_id=institution_id,
            period_id=period_id,
            name=name,
            status="running",
            solver_config={
                "max_time_seconds": solver_config.max_time_seconds,
                "num_workers": solver_config.num_workers,
                "gap_tolerance": solver_config.gap_tolerance,
            },
            started_at=started_at,
            created_by=created_by,
        )
        with self._uow:
            saved = self._uow.schedule_runs.save(run)
            self._uow.commit()
        return saved

    def _mark_error(
        self,
        run_id: EntityId,
        exc: BaseException | None = None,
    ) -> None:
        """Set the run status to 'error' and record failure metadata."""
        try:
            with self._uow:
                run = self._uow.schedule_runs.get_by_id(run_id)
                if run is not None:
                    run.status = "error"
                    run.completed_at = datetime.now(timezone.utc)
                    if exc is not None:
                        run.statistics = {
                            **run.statistics,
                            "error": {
                                "type": type(exc).__name__,
                                "message": str(exc),
                                "traceback": "".join(
                                    tb_module.format_exception(
                                        type(exc), exc, exc.__traceback__,
                                    ),
                                ),
                            },
                        }
                    self._uow.schedule_runs.save(run)
                    self._uow.commit()
        except Exception:
            _logger.exception("Failed to mark run %s as error", run_id)
