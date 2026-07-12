"""Tests for execution tracking, result publishing, and schedule generation pipeline."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest

from app.application.services.execution_tracker import (
    ExecutionStage,
    ExecutionTracker,
)
from app.application.services.result_publisher import ResultPublisher
from app.application.queries.schedule_queries import (
    GetExecutionLogs,
    GetScheduleRunDetail,
)
from app.domain.entities.schedule import ExecutionLog, ScheduleRun
from app.solver.config import SolverStatus
from app.solver.result import (
    AssignmentResult,
    OptimizationResult,
    SessionResult,
    SolverStatistics,
)
from tests.conftest import make_id


class TestExecutionStage:
    def test_all_ten_stages_exist(self) -> None:
        assert len(ExecutionStage) == 10

    def test_stage_values(self) -> None:
        expected = [
            "inicializando", "validando", "construyendo_modelo",
            "generando_variables", "aplicando_restricciones",
            "optimizando", "extrayendo_solucion", "guardando",
            "publicado", "error",
        ]
        assert [s.value for s in ExecutionStage] == expected


class TestExecutionTracker:
    def test_begin_persists_event(self, mock_uow: MagicMock) -> None:
        run_id = make_id()
        tracker = ExecutionTracker(mock_uow, run_id)

        tracker.begin(ExecutionStage.INICIALIZANDO)

        mock_uow.execution_logs.save.assert_called_once()
        saved = mock_uow.execution_logs.save.call_args[0][0]
        assert saved.event_type == "stage_transition"
        assert saved.schedule_run_id == run_id
        assert "inicializando" in saved.message

    def test_advance_records_elapsed(self, mock_uow: MagicMock) -> None:
        tracker = ExecutionTracker(mock_uow, make_id())
        tracker.begin(ExecutionStage.INICIALIZANDO)
        tracker.advance(ExecutionStage.VALIDANDO)

        assert "inicializando" in tracker.timings
        assert tracker.timings["inicializando"] >= 0

    def test_complete_records_total_timing(self, mock_uow: MagicMock) -> None:
        tracker = ExecutionTracker(mock_uow, make_id())
        tracker.begin(ExecutionStage.INICIALIZANDO)
        tracker.advance(ExecutionStage.VALIDANDO)
        tracker.complete()

        assert "total" in tracker.timings
        assert tracker.timings["total"] >= 0

    def test_fail_records_traceback(self, mock_uow: MagicMock) -> None:
        tracker = ExecutionTracker(mock_uow, make_id())
        tracker.begin(ExecutionStage.OPTIMIZANDO)

        try:
            raise ValueError("solver exploded")
        except ValueError as exc:
            tracker.fail(exc)

        last_save = mock_uow.execution_logs.save.call_args_list[-1]
        saved = last_save[0][0]
        assert saved.event_type == "error"
        assert "solver exploded" in saved.message
        assert "traceback" in saved.metadata
        assert "ValueError" in saved.metadata["error_type"]

    def test_log_event_custom(self, mock_uow: MagicMock) -> None:
        tracker = ExecutionTracker(mock_uow, make_id())
        tracker.begin(ExecutionStage.CONSTRUYENDO_MODELO)
        tracker.log_event("execution", "Built 50 groups", {"groups": 50})

        calls = mock_uow.execution_logs.save.call_args_list
        custom_call = calls[-1][0][0]
        assert custom_call.event_type == "execution"
        assert custom_call.metadata["groups"] == 50

    def test_persist_failure_does_not_raise(self, mock_uow: MagicMock) -> None:
        mock_uow.execution_logs.save.side_effect = RuntimeError("db down")
        tracker = ExecutionTracker(mock_uow, make_id())
        tracker.begin(ExecutionStage.INICIALIZANDO)


class TestResultPublisher:
    def _make_stats(self) -> SolverStatistics:
        return SolverStatistics(
            groups_total=10,
            groups_scheduled=8,
            instructors_total=5,
            rooms_total=3,
            time_slots_total=55,
            num_variables=500,
            num_constraints=200,
            variables_by_category={"X": 100, "Y": 200, "Z": 200},
            constraints_by_type={"HD-01": 50, "SB-01": 30},
            hard_constraints_total=50,
            soft_constraints_total=30,
            elapsed_seconds=12.5,
            timings={"model_build": 1.5, "solve": 10.0, "total": 12.5},
            memory_usage_mb=128.5,
            objective_value=950.0,
            gap=0.02,
            workload_spread=1.5,
            avg_preference_score=7.2,
            room_utilization_pct=65.0,
        )

    def test_publish_saves_comprehensive_statistics(
        self, mock_uow: MagicMock,
    ) -> None:
        run = ScheduleRun(id=make_id(), status="running")
        mock_uow.schedule_runs.get_by_id.return_value = run

        stats = self._make_stats()
        result = OptimizationResult(
            status=SolverStatus.OPTIMAL,
            assignments=[],
            statistics=stats,
        )

        ResultPublisher(mock_uow).publish(result, run.id)

        saved_run = mock_uow.schedule_runs.save.call_args[0][0]
        s = saved_run.statistics

        assert s["groups_total"] == 10
        assert s["groups_scheduled"] == 8
        assert s["variables_by_category"] == {"X": 100, "Y": 200, "Z": 200}
        assert s["constraints_by_type"] == {"HD-01": 50, "SB-01": 30}
        assert s["hard_constraints_total"] == 50
        assert s["soft_constraints_total"] == 30
        assert s["timings"] == {"model_build": 1.5, "solve": 10.0, "total": 12.5}
        assert s["memory_usage_mb"] == 128.5
        assert s["workload_spread"] == 1.5
        assert s["avg_preference_score"] == 7.2
        assert s["room_utilization_pct"] == 65.0

    def test_publish_persists_assignments(
        self, mock_uow: MagicMock,
    ) -> None:
        run = ScheduleRun(id=make_id(), status="running")
        mock_uow.schedule_runs.get_by_id.return_value = run

        result = OptimizationResult(
            status=SolverStatus.FEASIBLE,
            assignments=[
                AssignmentResult(
                    group_id=make_id(),
                    instructor_id=make_id(),
                    sessions=[
                        SessionResult(
                            block_index=0, day_of_week=1,
                            start_period=1, duration=2,
                            classroom_id=make_id(),
                        ),
                    ],
                ),
            ],
            statistics=SolverStatistics(),
        )

        ResultPublisher(mock_uow).publish(result, run.id)

        mock_uow.assignments.save.assert_called_once()
        mock_uow.session_blocks.save.assert_called_once()
        mock_uow.commit.assert_called_once()

    def test_publish_infeasible_no_assignments(
        self, mock_uow: MagicMock,
    ) -> None:
        run = ScheduleRun(id=make_id(), status="running")
        mock_uow.schedule_runs.get_by_id.return_value = run

        result = OptimizationResult.infeasible(["No solution found"])

        ResultPublisher(mock_uow).publish(result, run.id)

        mock_uow.assignments.save.assert_not_called()
        saved_run = mock_uow.schedule_runs.save.call_args[0][0]
        assert saved_run.status == "infeasible"


class TestGetExecutionLogs:
    def test_returns_logs_for_run(self, mock_uow: MagicMock) -> None:
        run_id = make_id()
        run = ScheduleRun(id=run_id)
        mock_uow.schedule_runs.get_by_id.return_value = run

        log1 = ExecutionLog(
            id=make_id(), schedule_run_id=run_id,
            event_type="stage_transition", message="Etapa: inicializando",
            timestamp=datetime.now(timezone.utc),
        )
        log2 = ExecutionLog(
            id=make_id(), schedule_run_id=run_id,
            event_type="stage_transition", message="Etapa: validando",
            timestamp=datetime.now(timezone.utc),
        )
        mock_uow.execution_logs.list_by_run.return_value = [log1, log2]

        result = GetExecutionLogs(mock_uow).execute(run_id)

        assert len(result) == 2
        assert result[0]["event_type"] == "stage_transition"
        assert "inicializando" in result[0]["message"]

    def test_raises_not_found(self, mock_uow: MagicMock) -> None:
        from app.application.exceptions import ResourceNotFoundError

        mock_uow.schedule_runs.get_by_id.return_value = None

        with pytest.raises(ResourceNotFoundError):
            GetExecutionLogs(mock_uow).execute(make_id())


class TestGetScheduleRunDetailWithLogs:
    def test_includes_execution_logs(self, mock_uow: MagicMock) -> None:
        run_id = make_id()
        run = ScheduleRun(id=run_id, status="optimal")
        mock_uow.schedule_runs.get_by_id.return_value = run
        mock_uow.assignments.list_by_schedule_run.return_value = []

        log = ExecutionLog(
            id=make_id(), schedule_run_id=run_id,
            event_type="stage_transition", message="Etapa: publicado",
            timestamp=datetime.now(timezone.utc),
        )
        mock_uow.execution_logs.list_by_run.return_value = [log]

        result = GetScheduleRunDetail(mock_uow).execute(run_id)

        assert "execution_logs" in result
        assert len(result["execution_logs"]) == 1
        assert result["execution_logs"][0]["event_type"] == "stage_transition"
