"""Tracks solver execution stages and persists event logs.

Each stage transition is recorded as an ExecutionLog entry with timing
metadata, enabling the frontend to display real-time progress and the
backend to capture detailed execution history for diagnostics.
"""

from __future__ import annotations

import time
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from app.core.logging.logger import get_logger
from app.core.utils.types import EntityId, generate_id
from app.domain.entities.schedule import ExecutionLog

if TYPE_CHECKING:
    from app.domain.interfaces.unit_of_work import UnitOfWork

__all__ = ["ExecutionStage", "ExecutionTracker"]

_logger = get_logger(__name__)


class ExecutionStage(Enum):
    """The 10 stages of a solver execution pipeline."""

    INICIALIZANDO = "inicializando"
    VALIDANDO = "validando"
    CONSTRUYENDO_MODELO = "construyendo_modelo"
    GENERANDO_VARIABLES = "generando_variables"
    APLICANDO_RESTRICCIONES = "aplicando_restricciones"
    OPTIMIZANDO = "optimizando"
    EXTRAYENDO_SOLUCION = "extrayendo_solucion"
    GUARDANDO = "guardando"
    PUBLICADO = "publicado"
    ERROR = "error"


class ExecutionTracker:
    """Records execution stage transitions for a solver run.

    Usage::

        tracker = ExecutionTracker(uow, run_id)
        tracker.begin(ExecutionStage.INICIALIZANDO)
        # ... do work ...
        tracker.advance(ExecutionStage.VALIDANDO)
        # ... do work ...
        tracker.complete()  # marks PUBLICADO

    On error::

        tracker.fail(exception, stage_at_failure)
    """

    def __init__(self, uow: UnitOfWork, run_id: EntityId) -> None:
        self._uow = uow
        self._run_id = run_id
        self._stage_start: float = time.monotonic()
        self._pipeline_start: float = time.monotonic()
        self._current_stage: ExecutionStage | None = None
        self._timings: dict[str, float] = {}

    @property
    def timings(self) -> dict[str, float]:
        """Return accumulated stage timings."""
        return dict(self._timings)

    def begin(self, stage: ExecutionStage) -> None:
        """Start tracking from the given initial stage."""
        self._pipeline_start = time.monotonic()
        self._transition(stage)

    def advance(self, stage: ExecutionStage) -> None:
        """Transition to the next stage, recording elapsed time for the previous one."""
        self._record_elapsed()
        self._transition(stage)

    def complete(self) -> None:
        """Mark the pipeline as successfully completed."""
        self._record_elapsed()
        total = time.monotonic() - self._pipeline_start
        self._timings["total"] = round(total, 4)
        self._persist_event(
            event_type="stage_transition",
            message=f"Pipeline completado en {total:.2f}s",
            metadata={"stage": ExecutionStage.PUBLICADO.value, "timings": self._timings},
        )
        self._current_stage = ExecutionStage.PUBLICADO
        _logger.info(
            "Pipeline completed for run %s — %.2fs total",
            self._run_id, total,
        )

    def fail(
        self,
        exc: BaseException,
        stage: ExecutionStage | None = None,
    ) -> None:
        """Record an error with traceback and the stage where it occurred."""
        self._record_elapsed()
        failed_stage = stage or self._current_stage or ExecutionStage.ERROR
        total = time.monotonic() - self._pipeline_start
        self._timings["total"] = round(total, 4)

        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)

        self._persist_event(
            event_type="error",
            message=f"Error en etapa '{failed_stage.value}': {exc}",
            metadata={
                "stage": failed_stage.value,
                "error_type": type(exc).__name__,
                "traceback": "".join(tb),
                "timings": self._timings,
            },
        )
        self._current_stage = ExecutionStage.ERROR
        _logger.error(
            "Pipeline failed at stage '%s' for run %s: %s",
            failed_stage.value, self._run_id, exc,
        )

    def log_event(
        self,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an arbitrary event within the current stage."""
        extra = metadata or {}
        if self._current_stage is not None:
            extra.setdefault("stage", self._current_stage.value)
        self._persist_event(event_type=event_type, message=message, metadata=extra)

    # ── private ──────────────────────────────────────────────────────

    def _transition(self, stage: ExecutionStage) -> None:
        self._current_stage = stage
        self._stage_start = time.monotonic()
        self._persist_event(
            event_type="stage_transition",
            message=f"Etapa: {stage.value}",
            metadata={"stage": stage.value},
        )
        _logger.info("Run %s → stage '%s'", self._run_id, stage.value)

    def _record_elapsed(self) -> None:
        if self._current_stage is not None:
            elapsed = time.monotonic() - self._stage_start
            self._timings[self._current_stage.value] = round(elapsed, 4)

    def _persist_event(
        self,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = ExecutionLog(
            id=generate_id(),
            schedule_run_id=self._run_id,
            event_type=event_type,
            message=message,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        try:
            with self._uow:
                self._uow.execution_logs.save(entry)
                self._uow.commit()
        except Exception:
            _logger.warning(
                "Failed to persist execution log for run %s", self._run_id,
                exc_info=True,
            )
